from django.db import models
from django.db.models import CheckConstraint, Q, Index
from django.conf import settings
from django.db.models import Sum, F
from django.utils import timezone
from students.models import Student, Semester
from academics.models import CourseSection


class GradeScale(models.Model):
    """Indian 10-point grading scale (CBCS compliant)."""
    letter = models.CharField(max_length=2, unique=True)
    min_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Inclusive lower bound (0-100)")
    max_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Inclusive upper bound (0-100)")
    grade_points = models.DecimalField(max_digits=4, decimal_places=2, help_text="Grade points for the letter (0-10)")
    description = models.CharField(max_length=50, help_text="Grade description (e.g., Outstanding, Excellent)")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-grade_points']
        constraints = [
            CheckConstraint(
                check=Q(min_score__gte=0) & Q(max_score__lte=100) & Q(min_score__lte=models.F('max_score')),
                name='grade_scale_score_bounds_valid'
            ),
            CheckConstraint(
                check=Q(grade_points__gte=0),
                name='grade_scale_points_nonnegative'
            ),
        ]

    def __str__(self):
        return f"{self.letter} ({self.description}): {self.min_score}-{self.max_score}% => {self.grade_points} points"


class MidTermGrade(models.Model):
    """Mid-term grades for students in course sections."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='midterm_grades')
    course_section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='midterm_grades')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='midterm_grades')
    
    # Mid-term marks
    midterm_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Marks obtained by student")
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100, help_text="Total marks for the exam (e.g., 50, 100)")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Calculated percentage")
    midterm_grade = models.CharField(max_length=2, blank=True)
    midterm_grade_points = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    # Metadata
    evaluated_at = models.DateTimeField(default=timezone.now)
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['student', 'course_section', 'semester']
        ordering = ['student__roll_number', 'course_section']
        constraints = [
            CheckConstraint(check=Q(midterm_marks__gte=0), name='midterm_marks_nonnegative'),
            CheckConstraint(check=Q(total_marks__gt=0), name='total_marks_positive'),
            CheckConstraint(check=Q(midterm_marks__lte=models.F('total_marks')), name='midterm_marks_lte_total'),
        ]
        indexes = [
            Index(fields=['student']),
            Index(fields=['course_section']),
            Index(fields=['semester']),
        ]

    def __str__(self):
        return f"{self.student.roll_number} - {self.course_section} (Mid-term): {self.midterm_grade}"

    def compute_midterm_grade(self):
        """Calculate mid-term grade based on percentage."""
        if self.midterm_marks is None or self.total_marks is None or self.total_marks == 0:
            return
            
        # Calculate percentage
        self.percentage = round((self.midterm_marks / self.total_marks) * 100, 2)
        
        # Find matching grade scale based on percentage
        scale = GradeScale.objects.filter(
            is_active=True,
            min_score__lte=self.percentage,
            max_score__gte=self.percentage
        ).order_by('-grade_points').first()
        
        if scale:
            self.midterm_grade = scale.letter
            self.midterm_grade_points = scale.grade_points
        else:
            self.midterm_grade = ''
            self.midterm_grade_points = None

    def save(self, *args, **kwargs):
        self.compute_midterm_grade()
        super().save(*args, **kwargs)


class SemesterGrade(models.Model):
    """Final semester grades for students in course sections."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_grades')
    course_section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='semester_grades')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='semester_grades')
    
    # Final marks
    final_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Marks obtained by student")
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100, help_text="Total marks for the exam (e.g., 50, 100)")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Calculated percentage")
    final_grade = models.CharField(max_length=2, blank=True)
    final_grade_points = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(default=False)
    
    # Metadata
    evaluated_at = models.DateTimeField(default=timezone.now)
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['student', 'course_section', 'semester']
        ordering = ['student__roll_number', 'course_section']
        constraints = [
            CheckConstraint(check=Q(final_marks__gte=0), name='final_marks_nonnegative'),
            CheckConstraint(check=Q(total_marks__gt=0), name='final_total_marks_positive'),
            CheckConstraint(check=Q(final_marks__lte=models.F('total_marks')), name='final_marks_lte_total'),
        ]
        indexes = [
            Index(fields=['student']),
            Index(fields=['course_section']),
            Index(fields=['semester']),
            Index(fields=['passed']),
        ]

    def __str__(self):
        return f"{self.student.roll_number} - {self.course_section} (Final): {self.final_grade}"

    def compute_final_grade(self):
        """Calculate final grade based on percentage."""
        if self.final_marks is None or self.total_marks is None or self.total_marks == 0:
            return
            
        # Calculate percentage
        self.percentage = round((self.final_marks / self.total_marks) * 100, 2)
        
        # Find matching grade scale based on percentage
        scale = GradeScale.objects.filter(
            is_active=True,
            min_score__lte=self.percentage,
            max_score__gte=self.percentage
        ).order_by('-grade_points').first()
        
        if scale:
            self.final_grade = scale.letter
            self.final_grade_points = scale.grade_points
            self.passed = scale.grade_points > 0
        else:
            self.final_grade = ''
            self.final_grade_points = None
            self.passed = False

    def save(self, *args, **kwargs):
        self.compute_final_grade()
        super().save(*args, **kwargs)
        # Update semester SGPA
        semester_gpa, _ = SemesterGPA.objects.get_or_create(
            student=self.student, 
            semester=self.semester
        )
        semester_gpa.recalculate()
        # Update cumulative CGPA
        cumulative_gpa, _ = CumulativeGPA.objects.get_or_create(student=self.student)
        cumulative_gpa.recalculate()


class SemesterGPA(models.Model):
    """SGPA (Semester Grade Point Average) per semester per student."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_gpas')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='gpas')
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="Semester Grade Point Average")
    total_credits = models.PositiveIntegerField(default=0, help_text="Total credits earned in this semester")
    total_quality_points = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Total quality points earned")
    
    # Academic standing
    ACADEMIC_STANDING_CHOICES = [
        ('EXCELLENT', 'Excellent (SGPA ≥ 8.0)'),
        ('VERY_GOOD', 'Very Good (SGPA ≥ 7.0)'),
        ('GOOD', 'Good (SGPA ≥ 6.0)'),
        ('SATISFACTORY', 'Satisfactory (SGPA ≥ 5.0)'),
        ('PASS', 'Pass (SGPA ≥ 4.0)'),
        ('PROBATION', 'Academic Probation (SGPA < 4.0)'),
    ]
    academic_standing = models.CharField(max_length=20, choices=ACADEMIC_STANDING_CHOICES, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'semester']
        ordering = ['-semester__academic_year__year']
        verbose_name = "Semester GPA (SGPA)"
        verbose_name_plural = "Semester GPAs (SGPA)"

    def __str__(self):
        return f"{self.student.roll_number} - {self.semester}: SGPA {self.sgpa}"

    def recalculate(self):
        """Recalculate SGPA based on semester grades."""
        aggregates = SemesterGrade.objects.filter(
            student=self.student,
            semester=self.semester
        ).aggregate(
            total_quality_points=Sum(F('final_grade_points') * F('course_section__course__credits')),
            total_credits=Sum('course_section__course__credits'),
        )
        
        total_qp = aggregates['total_quality_points'] or 0
        total_credits = aggregates['total_credits'] or 0
        
        if total_credits:
            self.sgpa = round(total_qp / total_credits, 2)
            self.total_credits = int(total_credits)
            self.total_quality_points = total_qp
            self.academic_standing = self._calculate_academic_standing()
        else:
            self.sgpa = None
            self.total_credits = 0
            self.total_quality_points = 0
            self.academic_standing = ''
        
        self.save(update_fields=['sgpa', 'total_credits', 'total_quality_points', 'academic_standing', 'updated_at'])

    def _calculate_academic_standing(self):
        """Calculate academic standing based on SGPA."""
        if self.sgpa is None:
            return ''
        elif self.sgpa >= 8.0:
            return 'EXCELLENT'
        elif self.sgpa >= 7.0:
            return 'VERY_GOOD'
        elif self.sgpa >= 6.0:
            return 'GOOD'
        elif self.sgpa >= 5.0:
            return 'SATISFACTORY'
        elif self.sgpa >= 4.0:
            return 'PASS'
        else:
            return 'PROBATION'


class CumulativeGPA(models.Model):
    """CGPA (Cumulative Grade Point Average) for overall academic performance."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='cumulative_gpa')
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="Cumulative Grade Point Average")
    total_credits_earned = models.PositiveIntegerField(default=0, help_text="Total credits earned across all semesters")
    total_quality_points = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total quality points earned")
    
    # Academic classification
    CLASSIFICATION_CHOICES = [
        ('FIRST_CLASS_DISTINCTION', 'First Class with Distinction (CGPA ≥ 8.0)'),
        ('FIRST_CLASS', 'First Class (CGPA ≥ 7.0)'),
        ('SECOND_CLASS', 'Second Class (CGPA ≥ 6.0)'),
        ('PASS_CLASS', 'Pass Class (CGPA ≥ 4.0)'),
        ('FAIL', 'Fail (CGPA < 4.0)'),
    ]
    classification = models.CharField(max_length=30, choices=CLASSIFICATION_CHOICES, blank=True)
    
    # Graduation eligibility
    is_eligible_for_graduation = models.BooleanField(default=False)
    graduation_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cumulative GPA (CGPA)"
        verbose_name_plural = "Cumulative GPAs (CGPA)"

    def __str__(self):
        return f"{self.student.roll_number}: CGPA {self.cgpa} ({self.classification})"

    def recalculate(self):
        """Recalculate CGPA based on all semester grades."""
        aggregates = SemesterGrade.objects.filter(
            student=self.student
        ).aggregate(
            total_quality_points=Sum(F('final_grade_points') * F('course_section__course__credits')),
            total_credits=Sum('course_section__course__credits'),
        )
        
        total_qp = aggregates['total_quality_points'] or 0
        total_credits = aggregates['total_credits'] or 0
        
        if total_credits:
            self.cgpa = round(total_qp / total_credits, 2)
            self.total_credits_earned = int(total_credits)
            self.total_quality_points = total_qp
            self.classification = self._calculate_classification()
            self.is_eligible_for_graduation = self._check_graduation_eligibility()
        else:
            self.cgpa = None
            self.total_credits_earned = 0
            self.total_quality_points = 0
            self.classification = ''
            self.is_eligible_for_graduation = False
        
        self.save(update_fields=['cgpa', 'total_credits_earned', 'total_quality_points', 'classification', 'is_eligible_for_graduation', 'updated_at'])

    def _calculate_classification(self):
        """Calculate degree classification based on CGPA."""
        if self.cgpa is None:
            return ''
        elif self.cgpa >= 8.0:
            return 'FIRST_CLASS_DISTINCTION'
        elif self.cgpa >= 7.0:
            return 'FIRST_CLASS'
        elif self.cgpa >= 6.0:
            return 'SECOND_CLASS'
        elif self.cgpa >= 4.0:
            return 'PASS_CLASS'
        else:
            return 'FAIL'

    def _check_graduation_eligibility(self):
        """Check if student is eligible for graduation."""
        # Basic eligibility: CGPA >= 4.0 and minimum credits (can be customized)
        return self.cgpa is not None and self.cgpa >= 4.0