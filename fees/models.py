import uuid
from decimal import Decimal
from django.db import models
from django.db import transaction
from django.db.models import Q, CheckConstraint, Index
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class TimeStampedUUIDModel(models.Model):
    """Abstract base model with UUID primary key and timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FeeCategory(TimeStampedUUIDModel):
    """Fee categories like Tuition, Library, Sports, etc."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = "Fee Categories"
    
    def __str__(self):
        return self.name


class FeeStructure(TimeStampedUUIDModel):
    """Fee structure for different academic years and grades"""
    
    ACADEMIC_YEAR_CHOICES = [
        ('2023-2024', '2023-2024'),
        ('2024-2025', '2024-2025'),
        ('2025-2026', '2025-2026'),
        ('2026-2027', '2026-2027'),
    ]
    
    GRADE_CHOICES = [
        ('1', 'Grade 1'),
        ('2', 'Grade 2'),
        ('3', 'Grade 3'),
        ('4', 'Grade 4'),
        ('5', 'Grade 5'),
        ('6', 'Grade 6'),
        ('7', 'Grade 7'),
        ('8', 'Grade 8'),
        ('9', 'Grade 9'),
        ('10', 'Grade 10'),
        ('11', 'Grade 11'),
        ('12', 'Grade 12'),
    ]
    
    name = models.CharField(max_length=200)
    academic_year = models.CharField(max_length=9, choices=ACADEMIC_YEAR_CHOICES)
    grade_level = models.CharField(max_length=2, choices=GRADE_CHOICES)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['academic_year', 'grade_level']
        ordering = ['academic_year', 'grade_level']
    
    def __str__(self):
        return f"{self.name} - {self.academic_year} - Grade {self.grade_level}"


class FeeStructureDetail(TimeStampedUUIDModel):
    """Individual fee items within a fee structure"""
    
    FREQUENCY_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('SEMESTER', 'Semester'),
        ('ANNUAL', 'Annual'),
        ('ONE_TIME', 'One Time'),
    ]
    
    fee_structure = models.ForeignKey(
        FeeStructure, 
        on_delete=models.CASCADE, 
        related_name='fee_details'
    )
    fee_category = models.ForeignKey(
        FeeCategory, 
        on_delete=models.CASCADE, 
        related_name='structure_details'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_optional = models.BooleanField(default=False)
    due_date = models.DateField(blank=True, null=True)
    late_fee_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    late_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    
    class Meta:
        unique_together = ['fee_structure', 'fee_category']
        ordering = ['fee_category__display_order']
    
    def __str__(self):
        return f"{self.fee_structure} - {self.fee_category} - {self.amount}"


class StudentFee(TimeStampedUUIDModel):
    """Individual student fee records"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partially Paid'),
        ('OVERDUE', 'Overdue'),
        ('WAIVED', 'Waived'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='fees'
    )
    fee_structure_detail = models.ForeignKey(
        FeeStructureDetail, 
        on_delete=models.CASCADE, 
        related_name='student_fees'
    )
    academic_year = models.CharField(max_length=9)
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    late_fee_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'fee_structure_detail', 'academic_year']
        ordering = ['due_date', 'student__roll_number']
        constraints = [
            CheckConstraint(check=Q(amount_due__gte=0), name='student_fee_amount_due_nonnegative'),
            CheckConstraint(check=Q(amount_paid__gte=0), name='student_fee_amount_paid_nonnegative'),
            CheckConstraint(check=Q(late_fee_amount__gte=0), name='student_fee_late_fee_nonnegative'),
        ]
        indexes = [
            Index(fields=['student', 'status']),
            Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.fee_structure_detail} - {self.status}"
    
    @property
    def balance_amount(self):
        """Calculate remaining balance"""
        from decimal import Decimal
        amount_due = self.amount_due if self.amount_due is not None else Decimal('0.00')
        amount_paid = self.amount_paid if self.amount_paid is not None else Decimal('0.00')
        return amount_due - amount_paid
    
    @property
    def is_overdue(self):
        """Check if fee is overdue"""
        if not self.due_date:
            return False
        today = timezone.now().date()
        return self.due_date < today and self.status == 'PENDING'
    
    @property
    def total_amount_due(self):
        """Total amount including late fees"""
        from decimal import Decimal
        amount_due = self.amount_due if self.amount_due is not None else Decimal('0.00')
        late_fee = self.late_fee_amount if self.late_fee_amount is not None else Decimal('0.00')
        return amount_due + late_fee


class Payment(TimeStampedUUIDModel):
    """Payment records for student fees"""
    
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('ONLINE', 'Online Payment'),
        ('CARD', 'Credit/Debit Card'),
        ('UPI', 'UPI'),
        ('OTHER', 'Other'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    student_fee = models.ForeignKey(
        StudentFee, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField(default=timezone.now)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    collected_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='collected_payments'
    )
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.student_fee.student.roll_number} - {self.amount} - {self.payment_date.date()}"
    
    def save(self, *args, **kwargs):
        # Collision-safe receipt generation with retries, and atomic aggregation update
        max_retries = 3
        for _ in range(max_retries):
            try:
                with transaction.atomic():
                    if not self.receipt_number:
                        # Use time + random suffix to avoid contention, keep uniqueness at DB level
                        ts = timezone.now().strftime('%Y%m%d%H%M%S%f')
                        import secrets
                        self.receipt_number = f"RCPT{ts}-{secrets.token_hex(3).upper()}"
                    super().save(*args, **kwargs)

                    if self.status == 'COMPLETED':
                        # Recompute paid aggregate safely
                        total_paid = self.student_fee.payments.filter(
                            status='COMPLETED'
                        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
                        self.student_fee.amount_paid = total_paid
                        if self.student_fee.amount_paid >= self.student_fee.amount_due:
                            self.student_fee.status = 'PAID'
                        elif self.student_fee.amount_paid > 0:
                            self.student_fee.status = 'PARTIAL'
                        self.student_fee.save(update_fields=['amount_paid', 'status'])
                break
            except Exception as e:
                # Retry on potential unique collisions
                self.receipt_number = None
                continue


class FeeWaiver(TimeStampedUUIDModel):
    """Fee waivers for students"""
    
    WAIVER_TYPE_CHOICES = [
        ('SCHOLARSHIP', 'Scholarship'),
        ('FINANCIAL_AID', 'Financial Aid'),
        ('MERIT', 'Merit Based'),
        ('SPORTS', 'Sports Quota'),
        ('DISABILITY', 'Disability'),
        ('OTHER', 'Other'),
    ]
    
    student_fee = models.ForeignKey(
        StudentFee, 
        on_delete=models.CASCADE, 
        related_name='waivers'
    )
    waiver_type = models.CharField(max_length=20, choices=WAIVER_TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    reason = models.TextField()
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_waivers'
    )
    approved_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student_fee.student.roll_number} - {self.waiver_type} - {self.amount}"


class FeeDiscount(TimeStampedUUIDModel):
    """Fee discounts for early payments or other reasons"""
    
    DISCOUNT_TYPE_CHOICES = [
        ('EARLY_PAYMENT', 'Early Payment'),
        ('SIBLING', 'Sibling Discount'),
        ('STAFF_CHILD', 'Staff Child'),
        ('BULK_PAYMENT', 'Bulk Payment'),
        ('LOYALTY', 'Loyalty Discount'),
        ('OTHER', 'Other'),
    ]
    
    student_fee = models.ForeignKey(
        StudentFee, 
        on_delete=models.CASCADE, 
        related_name='discounts'
    )
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    reason = models.TextField()
    valid_until = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student_fee.student.roll_number} - {self.discount_type} - {self.amount}"


class FeeReceipt(TimeStampedUUIDModel):
    """Generated fee receipts for payments"""
    
    student_fee = models.ForeignKey(
        StudentFee, 
        on_delete=models.CASCADE, 
        related_name='receipts'
    )
    payment = models.ForeignKey(
        Payment, 
        on_delete=models.CASCADE, 
        related_name='receipts'
    )
    receipt_number = models.CharField(max_length=50, unique=True)
    generated_date = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='generated_receipts'
    )
    is_printed = models.BooleanField(default=False)
    printed_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-generated_date']
    
    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.student_fee.student.roll_number}"
