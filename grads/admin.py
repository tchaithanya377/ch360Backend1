from django.contrib import admin
from .models import GradeScale, Term, CourseResult, TermGPA, GraduateRecord


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ('letter', 'min_score', 'max_score', 'grade_points', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('letter',)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'semester', 'start_date', 'end_date', 'is_locked')
    list_filter = ('academic_year', 'semester', 'is_locked')
    search_fields = ('name', 'academic_year')


@admin.register(CourseResult)
class CourseResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'course_section', 'total_marks', 'letter_grade', 'grade_points', 'passed')
    list_filter = ('term__academic_year', 'term__semester', 'passed', 'letter_grade')
    search_fields = ('student__roll_number', 'course_section__course__code')
    autocomplete_fields = ('student', 'term', 'course_section', 'evaluator')


@admin.register(TermGPA)
class TermGPAAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'gpa', 'total_credits')
    list_filter = ('term__academic_year', 'term__semester')
    search_fields = ('student__roll_number',)


@admin.register(GraduateRecord)
class GraduateRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'program', 'cgpa', 'total_credits_earned', 'graduation_date')
    list_filter = ('program__level',)
    search_fields = ('student__roll_number',)

# Register your models here.
