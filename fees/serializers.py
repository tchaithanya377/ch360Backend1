from rest_framework import serializers
from django.db.models import Sum
from .models import (
    FeeCategory, FeeStructure, FeeStructureDetail, StudentFee,
    Payment, FeeWaiver, FeeDiscount, FeeReceipt
)


class FeeCategorySerializer(serializers.ModelSerializer):
    """Serializer for FeeCategory model"""
    
    class Meta:
        model = FeeCategory
        fields = [
            'id', 'name', 'description', 'is_active', 'display_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FeeStructureSerializer(serializers.ModelSerializer):
    """Serializer for FeeStructure model"""
    
    total_amount = serializers.SerializerMethodField()
    fee_details_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FeeStructure
        fields = [
            'id', 'name', 'academic_year', 'grade_level', 'is_active',
            'description', 'total_amount', 'fee_details_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_amount(self, obj):
        total = obj.fee_details.aggregate(total=Sum('amount'))['total'] or 0
        return str(total)
    
    def get_fee_details_count(self, obj):
        return obj.fee_details.count()


class FeeStructureDetailSerializer(serializers.ModelSerializer):
    """Serializer for FeeStructureDetail model"""
    
    fee_structure = FeeStructureSerializer(read_only=True)
    fee_category = FeeCategorySerializer(read_only=True)
    fee_structure_id = serializers.UUIDField(write_only=True)
    fee_category_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = FeeStructureDetail
        fields = [
            'id', 'fee_structure', 'fee_category', 'fee_structure_id',
            'fee_category_id', 'amount', 'frequency', 'is_optional',
            'due_date', 'late_fee_amount', 'late_fee_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentFeeSerializer(serializers.ModelSerializer):
    """Serializer for StudentFee model"""
    
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    student_name = serializers.SerializerMethodField()
    fee_category_name = serializers.CharField(source='fee_structure_detail.fee_category.name', read_only=True)
    fee_structure_name = serializers.CharField(source='fee_structure_detail.fee_structure.name', read_only=True)
    balance_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    total_amount_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = StudentFee
        fields = [
            'id', 'student', 'student_roll_number', 'student_name',
            'fee_structure_detail', 'fee_category_name', 'fee_structure_name',
            'academic_year', 'due_date', 'amount_due', 'amount_paid',
            'late_fee_amount', 'status', 'notes', 'balance_amount',
            'is_overdue', 'total_amount_due', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'student_roll_number', 'student_name', 'fee_category_name',
            'fee_structure_name', 'balance_amount', 'is_overdue', 'total_amount_due',
            'created_at', 'updated_at'
        ]
    
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
    
    def validate(self, data):
        # Validate that amount_paid cannot exceed amount_due
        if 'amount_paid' in data and data['amount_paid'] > data['amount_due']:
            raise serializers.ValidationError("Amount paid cannot exceed amount due")
        
        # Validate due_date is not in the past when creating
        if self.instance is None and 'due_date' in data:
            from django.utils import timezone
            if data['due_date'] < timezone.now().date():
                raise serializers.ValidationError("Due date cannot be in the past")
        
        return data


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    student_roll_number = serializers.CharField(source='student_fee.student.roll_number', read_only=True)
    student_name = serializers.CharField(source='student_fee.student.first_name', read_only=True)
    fee_category = serializers.CharField(source='student_fee.fee_structure_detail.fee_category.name', read_only=True)
    collected_by_username = serializers.CharField(source='collected_by.username', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'student_fee', 'student_roll_number', 'student_name',
            'fee_category', 'amount', 'payment_method', 'payment_date',
            'transaction_id', 'reference_number', 'status', 'receipt_number',
            'notes', 'collected_by', 'collected_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'receipt_number', 'student_roll_number', 'student_name',
            'fee_category', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        # Validate that payment amount doesn't exceed remaining balance
        if 'amount' in data and 'student_fee' in data:
            student_fee = data['student_fee']
            remaining_balance = student_fee.balance_amount
            if data['amount'] > remaining_balance:
                raise serializers.ValidationError(
                    f"Payment amount cannot exceed remaining balance of ₹{remaining_balance}"
                )
        
        return data


class FeeWaiverSerializer(serializers.ModelSerializer):
    """Serializer for FeeWaiver model"""
    
    student_roll_number = serializers.CharField(source='student_fee.student.roll_number', read_only=True)
    student_name = serializers.CharField(source='student_fee.student.first_name', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = FeeWaiver
        fields = [
            'id', 'student_fee', 'student_roll_number', 'student_name',
            'waiver_type', 'amount', 'percentage', 'reason', 'approved_by',
            'approved_by_username', 'approved_date', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'student_roll_number', 'student_name', 'approved_by_username',
            'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        # Validate that waiver amount doesn't exceed fee amount
        if 'amount' in data and 'student_fee' in data:
            student_fee = data['student_fee']
            if data['amount'] > student_fee.amount_due:
                raise serializers.ValidationError(
                    "Waiver amount cannot exceed the fee amount due"
                )
        
        return data


class FeeDiscountSerializer(serializers.ModelSerializer):
    """Serializer for FeeDiscount model"""
    
    student_roll_number = serializers.CharField(source='student_fee.student.roll_number', read_only=True)
    student_name = serializers.CharField(source='student_fee.student.first_name', read_only=True)
    
    class Meta:
        model = FeeDiscount
        fields = [
            'id', 'student_fee', 'student_roll_number', 'student_name',
            'discount_type', 'amount', 'percentage', 'reason', 'valid_until',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'student_roll_number', 'student_name',
            'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        # Validate that discount amount doesn't exceed fee amount
        if 'amount' in data and 'student_fee' in data:
            student_fee = data['student_fee']
            if data['amount'] > student_fee.amount_due:
                raise serializers.ValidationError(
                    "Discount amount cannot exceed the fee amount due"
                )
        
        return data


class FeeReceiptSerializer(serializers.ModelSerializer):
    """Serializer for FeeReceipt model"""
    
    student_roll_number = serializers.CharField(source='student_fee.student.roll_number', read_only=True)
    student_name = serializers.CharField(source='student_fee.student.first_name', read_only=True)
    payment_amount = serializers.DecimalField(source='payment.amount', max_digits=10, decimal_places=2, read_only=True)
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = FeeReceipt
        fields = [
            'id', 'student_fee', 'payment', 'student_roll_number', 'student_name',
            'payment_amount', 'receipt_number', 'generated_date', 'generated_by',
            'generated_by_username', 'is_printed', 'printed_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'receipt_number', 'generated_date', 'generated_by_username',
            'created_at', 'updated_at'
        ]


# Nested serializers for detailed views
class FeeStructureDetailNestedSerializer(FeeStructureDetailSerializer):
    """Nested serializer for FeeStructureDetail with full fee structure info"""
    
    fee_structure = FeeStructureSerializer()
    fee_category = FeeCategorySerializer()


class StudentFeeNestedSerializer(StudentFeeSerializer):
    """Nested serializer for StudentFee with full details"""
    
    fee_structure_detail = FeeStructureDetailNestedSerializer()


class PaymentNestedSerializer(PaymentSerializer):
    """Nested serializer for Payment with full details"""
    
    student_fee = StudentFeeSerializer()


# Summary serializers for dashboard
class FeeSummarySerializer(serializers.Serializer):
    """Serializer for fee summary statistics"""
    
    total_students = serializers.IntegerField()
    total_fees_due = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_fees_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    overdue_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    paid_count = serializers.IntegerField()


class StudentFeeSummarySerializer(serializers.Serializer):
    """Serializer for individual student fee summary"""
    
    student_id = serializers.UUIDField()
    roll_number = serializers.CharField()
    student_name = serializers.CharField()
    total_fees_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_fees_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    last_payment_date = serializers.DateTimeField(allow_null=True)
