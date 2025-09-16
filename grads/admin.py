from django.contrib import admin
from django.utils.html import format_html
from .models import GradeScale, MidTermGrade, SemesterGrade, SemesterGPA, CumulativeGPA


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ('letter', 'description', 'score_range', 'grade_points', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('letter', 'description')
    ordering = ['-grade_points']
    
    def score_range(self, obj):
        return f"{obj.min_score}-{obj.max_score}%"
    score_range.short_description = 'Score Range'


@admin.register(MidTermGrade)
class MidTermGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_section', 'semester', 'midterm_marks', 'total_marks', 'percentage', 'midterm_grade', 'midterm_grade_points', 'evaluated_at')
    list_filter = ('semester', 'course_section__course__department', 'evaluated_at', 'midterm_grade')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name', 'course_section__course__code')
    autocomplete_fields = ('student', 'course_section', 'evaluator')
    ordering = ['student__roll_number', 'course_section']
    readonly_fields = ('percentage', 'midterm_grade', 'midterm_grade_points', 'evaluated_at')
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Student & Course Information', {
                'fields': ('student', 'course_section', 'semester')
            }),
            ('Grade Information', {
                'fields': ('midterm_marks', 'total_marks', 'percentage', 'midterm_grade', 'midterm_grade_points'),
                'description': 'Enter marks obtained and total marks. Percentage, grade and points will be calculated automatically based on the grade scale.'
            }),
            ('Grade Scale Reference', {
                'fields': (),
                'description': self.get_grade_scale_preview(),
                'classes': ('collapse',)
            }),
            ('Evaluation Details', {
                'fields': ('evaluator', 'evaluated_at'),
                'classes': ('collapse',)
            }),
        )
        return fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('student', 'course_section', 'semester')
        return self.readonly_fields
    
    def get_grade_scale_preview(self):
        """Generate HTML preview of current grade scale"""
        scales = GradeScale.objects.filter(is_active=True).order_by('-grade_points')
        if not scales:
            return "No grade scales configured. Please add grade scales first."
        
        html = "<div style='background: #f8f9fa; padding: 10px; border-radius: 5px;'>"
        html += "<h4>Current Grade Scale:</h4><table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr style='background: #e9ecef;'><th style='padding: 5px; border: 1px solid #dee2e6;'>Grade</th><th style='padding: 5px; border: 1px solid #dee2e6;'>Score Range</th><th style='padding: 5px; border: 1px solid #dee2e6;'>Points</th></tr>"
        
        for scale in scales:
            html += f"<tr><td style='padding: 5px; border: 1px solid #dee2e6; text-align: center; font-weight: bold;'>{scale.letter}</td>"
            html += f"<td style='padding: 5px; border: 1px solid #dee2e6; text-align: center;'>{scale.min_score}-{scale.max_score}</td>"
            html += f"<td style='padding: 5px; border: 1px solid #dee2e6; text-align: center;'>{scale.grade_points}</td></tr>"
        
        html += "</table></div>"
        return format_html(html)


@admin.register(SemesterGrade)
class SemesterGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_section', 'semester', 'final_marks', 'total_marks', 'percentage', 'final_grade', 'final_grade_points', 'passed', 'evaluated_at')
    list_filter = ('semester', 'course_section__course__department', 'passed', 'evaluated_at', 'final_grade')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name', 'course_section__course__code')
    autocomplete_fields = ('student', 'course_section', 'evaluator')
    ordering = ['student__roll_number', 'course_section']
    readonly_fields = ('percentage', 'final_grade', 'final_grade_points', 'passed', 'evaluated_at')
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Student & Course Information', {
                'fields': ('student', 'course_section', 'semester')
            }),
            ('Grade Information', {
                'fields': ('final_marks', 'total_marks', 'percentage', 'final_grade', 'final_grade_points', 'passed'),
                'description': 'Enter marks obtained and total marks. Percentage, grade, points, and pass status will be calculated automatically based on the grade scale.'
            }),
            ('Grade Scale Reference', {
                'fields': (),
                'description': self.get_grade_scale_preview(),
                'classes': ('collapse',)
            }),
            ('Evaluation Details', {
                'fields': ('evaluator', 'evaluated_at'),
                'classes': ('collapse',)
            }),
        )
        return fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('student', 'course_section', 'semester')
        return self.readonly_fields
    
    def get_grade_scale_preview(self):
        """Generate HTML preview of current grade scale"""
        scales = GradeScale.objects.filter(is_active=True).order_by('-grade_points')
        if not scales:
            return "No grade scales configured. Please add grade scales first."
        
        html = "<div style='background: #f8f9fa; padding: 10px; border-radius: 5px;'>"
        html += "<h4>Current Grade Scale:</h4><table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr style='background: #e9ecef;'><th style='padding: 5px; border: 1px solid #dee2e6;'>Grade</th><th style='padding: 5px; border: 1px solid #dee2e6;'>Score Range</th><th style='padding: 5px; border: 1px solid #dee2e6;'>Points</th></tr>"
        
        for scale in scales:
            html += f"<tr><td style='padding: 5px; border: 1px solid #dee2e6; text-align: center; font-weight: bold;'>{scale.letter}</td>"
            html += f"<td style='padding: 5px; border: 1px solid #dee2e6; text-align: center;'>{scale.min_score}-{scale.max_score}</td>"
            html += f"<td style='padding: 5px; border: 1px solid #dee2e6; text-align: center;'>{scale.grade_points}</td></tr>"
        
        html += "</table></div>"
        return format_html(html)


@admin.register(SemesterGPA)
class SemesterGPAAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'sgpa', 'total_credits', 'academic_standing', 'updated_at')
    list_filter = ('semester', 'academic_standing')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name')
    autocomplete_fields = ('student', 'semester')
    ordering = ['-semester__academic_year__year', 'student__roll_number']
    readonly_fields = ('sgpa', 'total_credits', 'total_quality_points', 'academic_standing', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Student & Semester Information', {
            'fields': ('student', 'semester')
        }),
        ('SGPA Calculation', {
            'fields': ('sgpa', 'total_credits', 'total_quality_points', 'academic_standing'),
            'description': 'SGPA is automatically calculated from semester grades. Academic standing is determined by SGPA.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CumulativeGPA)
class CumulativeGPAAdmin(admin.ModelAdmin):
    list_display = ('student', 'cgpa', 'total_credits_earned', 'classification', 'is_eligible_for_graduation', 'updated_at')
    list_filter = ('classification', 'is_eligible_for_graduation')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name')
    autocomplete_fields = ('student',)
    ordering = ['-cgpa', 'student__roll_number']
    readonly_fields = ('cgpa', 'total_credits_earned', 'total_quality_points', 'classification', 'is_eligible_for_graduation', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('CGPA Calculation', {
            'fields': ('cgpa', 'total_credits_earned', 'total_quality_points', 'classification'),
            'description': 'CGPA is automatically calculated from all semester grades. Classification follows Indian university standards.'
        }),
        ('Graduation Information', {
            'fields': ('is_eligible_for_graduation', 'graduation_date'),
            'description': 'Graduation eligibility is automatically determined based on CGPA and credit requirements.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['recalculate_cgpa']
    
    def recalculate_cgpa(self, request, queryset):
        """Admin action to recalculate CGPA for selected students."""
        updated_count = 0
        for cgpa in queryset:
            cgpa.recalculate()
            updated_count += 1
        self.message_user(request, f'Successfully recalculated CGPA for {updated_count} students.')
    recalculate_cgpa.short_description = "Recalculate CGPA for selected students"