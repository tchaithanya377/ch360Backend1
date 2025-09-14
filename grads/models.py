from django.db import models
from django.conf import settings
from django.db.models import Sum, F
from django.utils import timezone
from students.models import Student
from academics.models import CourseSection, AcademicProgram
from departments.models import Department


class GradeScale(models.Model):
    """Letter grade mapping and boundaries, optionally scoped to department/program."""
    letter = models.CharField(max_length=2)
    min_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Inclusive lower bound (0-100)")
    max_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Inclusive upper bound (0-100)")
    grade_points = models.DecimalField(max_digits=4, decimal_places=2, help_text="Grade points for the letter (e.g., 10, 9)")
    is_active = models.BooleanField(default=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name='grade_scales')
    program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, null=True, blank=True, related_name='grade_scales')

    class Meta:
        ordering = ['-grade_points']
        unique_together = (
            ('letter', 'department', 'program'),
        )

    def __str__(self):
        scope = self.department.code if self.department_id else (self.program.code if self.program_id else 'GLOBAL')
        return f"{self.letter} [{scope}] {self.min_score}-{self.max_score} => {self.grade_points}"


class Term(models.Model):
    """Represents a semester/term instance."""
    SEMESTER_CHOICES = [
        ('FALL', 'Fall'),
        ('SPRING', 'Spring'),
        ('SUMMER', 'Summer'),
        ('WINTER', 'Winter'),
    ]

    name = models.CharField(max_length=100, help_text="Human-friendly term name")
    academic_year = models.CharField(max_length=9, help_text="e.g., 2024-2025")
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_locked = models.BooleanField(default=False, help_text="Lock after results are finalized")

    class Meta:
        unique_together = ['academic_year', 'semester']
        ordering = ['-academic_year', 'semester']

    def __str__(self):
        return f"{self.academic_year} {self.get_semester_display()}"


class GraduateRecord(models.Model):
    """Graduate status and aggregates per student/program."""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='graduate_record')
    program = models.ForeignKey(AcademicProgram, on_delete=models.SET_NULL, null=True, blank=True)
    graduation_date = models.DateField(null=True, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    total_credits_earned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GraduateRecord({self.student.roll_number})"

    def recalculate_cgpa(self):
        aggregates = CourseResult.objects.filter(student=self.student).aggregate(
            total_quality_points=Sum(F('grade_points') * F('course_section__course__credits')),
            total_credits=Sum('course_section__course__credits'),
        )
        total_qp = aggregates['total_quality_points'] or 0
        total_credits = aggregates['total_credits'] or 0
        if total_credits:
            self.cgpa = round(total_qp / total_credits, 2)
            self.total_credits_earned = int(total_credits)
        else:
            self.cgpa = None
            self.total_credits_earned = 0
        self.save(update_fields=['cgpa', 'total_credits_earned', 'updated_at'])


class TermGPA(models.Model):
    """GPA per term per student."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='term_gpas')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='gpas')
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    total_credits = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['student', 'term']
        ordering = ['-term__academic_year']

    def __str__(self):
        return f"{self.student.roll_number} - {self.term}: {self.gpa}"

    def recalculate(self):
        aggregates = CourseResult.objects.filter(student=self.student, term=self.term).aggregate(
            total_quality_points=Sum(F('grade_points') * F('course_section__course__credits')),
            total_credits=Sum('course_section__course__credits'),
        )
        total_qp = aggregates['total_quality_points'] or 0
        total_credits = aggregates['total_credits'] or 0
        if total_credits:
            self.gpa = round(total_qp / total_credits, 2)
            self.total_credits = int(total_credits)
        else:
            self.gpa = None
            self.total_credits = 0
        self.save(update_fields=['gpa', 'total_credits'])


class CourseResult(models.Model):
    """Marks/grade for a student in a course section for a given term."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='course_results')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='course_results')
    course_section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='course_results')
    internal_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    external_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    letter_grade = models.CharField(max_length=2, blank=True)
    grade_points = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(default=False)
    evaluated_at = models.DateTimeField(default=timezone.now)
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['student', 'term', 'course_section']
        ordering = ['student__roll_number', 'term__academic_year']

    def __str__(self):
        return f"{self.student.roll_number} - {self.course_section}"

    def compute_grade(self):
        self.total_marks = (self.internal_marks or 0) + (self.external_marks or 0)
        # Determine scoped grading policy: Department > Program > Global
        course = self.course_section.course
        dept = course.department_id
        scale_qs = GradeScale.objects.filter(is_active=True, min_score__lte=self.total_marks, max_score__gte=self.total_marks)
        scale = None
        if dept:
            scale = scale_qs.filter(department_id=dept).order_by('-grade_points').first()
        if not scale:
            program_ids = list(course.programs.values_list('id', flat=True))
            if program_ids:
                scale = scale_qs.filter(program_id__in=program_ids, department__isnull=True).order_by('-grade_points').first()
        if not scale:
            scale = scale_qs.filter(department__isnull=True, program__isnull=True).order_by('-grade_points').first()
        if scale:
            self.letter_grade = scale.letter
            self.grade_points = scale.grade_points
            self.passed = scale.grade_points > 0
        else:
            self.letter_grade = ''
            self.grade_points = None
            self.passed = False

    def save(self, *args, **kwargs):
        self.compute_grade()
        super().save(*args, **kwargs)
        # Update term GPA
        term_gpa, _ = TermGPA.objects.get_or_create(student=self.student, term=self.term)
        term_gpa.recalculate()
        # Ensure graduate record exists and update CGPA
        grad, _ = GraduateRecord.objects.get_or_create(student=self.student)
        grad.recalculate_cgpa()

    def delete(self, *args, **kwargs):
        student = self.student
        term = self.term
        super().delete(*args, **kwargs)
        term_gpa, _ = TermGPA.objects.get_or_create(student=student, term=term)
        term_gpa.recalculate()
        grad, _ = GraduateRecord.objects.get_or_create(student=student)
        grad.recalculate_cgpa()


# Create your models here.
