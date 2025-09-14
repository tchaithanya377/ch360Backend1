from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Q
from .models import (
    FeeCategory, FeeStructure, FeeStructureDetail, StudentFee,
    Payment, FeeWaiver, FeeDiscount, FeeReceipt
)


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'display_order']
    ordering = ['display_order', 'name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'grade_level', 'is_active', 'total_fees', 'created_at']
    list_filter = ['academic_year', 'grade_level', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['academic_year', 'grade_level']
    
    def total_fees(self, obj):
        total = obj.fee_details.aggregate(total=Sum('amount'))['total'] or 0
        return f"₹{total:,.2f}"
    total_fees.short_description = "Total Fees"
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('fee_details')


@admin.register(FeeStructureDetail)
class FeeStructureDetailAdmin(admin.ModelAdmin):
    list_display = [
        'fee_structure', 'fee_category', 'amount', 'frequency', 
        'is_optional', 'due_date', 'late_fee_amount'
    ]
    list_filter = ['frequency', 'is_optional', 'fee_structure__academic_year', 'fee_structure__grade_level']
    search_fields = ['fee_structure__name', 'fee_category__name']
    list_editable = ['amount', 'is_optional', 'late_fee_amount']
    ordering = ['fee_structure__academic_year', 'fee_structure__grade_level', 'fee_category__display_order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fee_structure', 'fee_category')


@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = [
        'student_roll', 'student_name', 'fee_category', 'academic_year', 
        'amount_due', 'amount_paid', 'balance', 'status', 'due_date', 'is_overdue_display'
    ]
    list_filter = [
        'status', 'academic_year', 'fee_structure_detail__fee_structure__grade_level',
        'due_date', 'created_at'
    ]
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name',
        'fee_structure_detail__fee_category__name'
    ]
    list_editable = ['status']
    readonly_fields = ['balance_amount', 'is_overdue', 'total_amount_due', 'notes']
    date_hierarchy = 'due_date'
    
    def student_roll(self, obj):
        return obj.student.roll_number
    student_roll.short_description = "Roll Number"
    student_roll.admin_order_field = 'student__roll_number'
    
    def student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
    student_name.short_description = "Student Name"
    student_name.admin_order_field = 'student__first_name'
    
    def fee_category(self, obj):
        return obj.fee_structure_detail.fee_category.name
    fee_category.short_description = "Fee Category"
    fee_category.admin_order_field = 'fee_structure_detail__fee_category__name'
    
    def balance(self, obj):
        balance = obj.balance_amount
        if balance > 0:
            return format_html('<span style="color: red;">₹{:.2f}</span>', balance)
        return format_html('<span style="color: green;">₹{:.2f}</span>', balance)
    balance.short_description = "Balance"
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">OVERDUE</span>')
        return format_html('<span style="color: green;">OK</span>')
    is_overdue_display.short_description = "Status"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'fee_structure_detail__fee_category', 'fee_structure_detail__fee_structure'
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'student_roll', 'student_name', 'amount', 
        'payment_method', 'payment_date', 'status', 'collected_by'
    ]
    list_filter = [
        'payment_method', 'status', 'payment_date', 'created_at',
        'student_fee__fee_structure_detail__fee_structure__academic_year'
    ]
    search_fields = [
        'receipt_number', 'transaction_id', 'reference_number',
        'student_fee__student__roll_number', 'student_fee__student__first_name'
    ]
    list_editable = ['status']
    readonly_fields = ['receipt_number', 'created_at', 'updated_at', 'notes']
    date_hierarchy = 'payment_date'
    
    def student_roll(self, obj):
        return obj.student_fee.student.roll_number
    student_roll.short_description = "Roll Number"
    student_roll.admin_order_field = 'student_fee__student__roll_number'
    
    def student_name(self, obj):
        student = obj.student_fee.student
        return f"{student.first_name} {student.last_name}"
    student_name.short_description = "Student Name"
    student_name.admin_order_field = 'student_fee__student__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student_fee__student', 'collected_by'
        )


@admin.register(FeeWaiver)
class FeeWaiverAdmin(admin.ModelAdmin):
    list_display = [
        'student_roll', 'student_name', 'waiver_type', 'amount', 
        'percentage', 'approved_by', 'approved_date', 'is_active'
    ]
    list_filter = ['waiver_type', 'is_active', 'approved_date', 'created_at']
    search_fields = [
        'student_fee__student__roll_number', 'student_fee__student__first_name',
        'reason', 'approved_by__username'
    ]
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    def student_roll(self, obj):
        return obj.student_fee.student.roll_number
    student_roll.short_description = "Roll Number"
    student_roll.admin_order_field = 'student_fee__student__roll_number'
    
    def student_name(self, obj):
        student = obj.student_fee.student
        return f"{student.first_name} {student.last_name}"
    student_name.short_description = "Student Name"
    student_name.admin_order_field = 'student_fee__student__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student_fee__student', 'approved_by'
        )


@admin.register(FeeDiscount)
class FeeDiscountAdmin(admin.ModelAdmin):
    list_display = [
        'student_roll', 'student_name', 'discount_type', 'amount', 
        'percentage', 'valid_until', 'is_active'
    ]
    list_filter = ['discount_type', 'is_active', 'valid_until', 'created_at']
    search_fields = [
        'student_fee__student__roll_number', 'student_fee__student__first_name',
        'reason'
    ]
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    def student_roll(self, obj):
        return obj.student_fee.student.roll_number
    student_roll.short_description = "Roll Number"
    student_roll.admin_order_field = 'student_fee__student__roll_number'
    
    def student_name(self, obj):
        student = obj.student_fee.student
        return f"{student.first_name} {student.last_name}"
    student_name.short_description = "Student Name"
    student_name.admin_order_field = 'student_fee__student__first_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student_fee__student')


@admin.register(FeeReceipt)
class FeeReceiptAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'student_roll', 'student_name', 'payment_amount',
        'generated_date', 'is_printed', 'printed_date', 'generated_by'
    ]
    list_filter = ['is_printed', 'generated_date', 'printed_date', 'created_at']
    search_fields = [
        'receipt_number', 'student_fee__student__roll_number',
        'student_fee__student__first_name'
    ]
    list_editable = ['is_printed']
    readonly_fields = ['receipt_number', 'generated_date', 'generated_by', 'created_at', 'updated_at']
    date_hierarchy = 'generated_date'
    
    def student_roll(self, obj):
        return obj.student_fee.student.roll_number
    student_roll.short_description = "Roll Number"
    student_roll.admin_order_field = 'student_fee__student__roll_number'
    
    def student_name(self, obj):
        student = obj.student_fee.student
        return f"{student.first_name} {student.last_name}"
    student_name.short_description = "Student Name"
    student_name.admin_order_field = 'student_fee__student__first_name'
    
    def payment_amount(self, obj):
        return f"₹{obj.payment.amount:,.2f}"
    payment_amount.short_description = "Payment Amount"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student_fee__student', 'payment', 'generated_by'
        )
