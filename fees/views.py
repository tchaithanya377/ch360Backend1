from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    FeeCategory, FeeStructure, FeeStructureDetail, StudentFee,
    Payment, FeeWaiver, FeeDiscount, FeeReceipt
)
from .serializers import (
    FeeCategorySerializer, FeeStructureSerializer, FeeStructureDetailSerializer,
    StudentFeeSerializer, PaymentSerializer, FeeWaiverSerializer,
    FeeDiscountSerializer, FeeReceiptSerializer, FeeSummarySerializer,
    StudentFeeSummarySerializer, FeeStructureDetailNestedSerializer,
    StudentFeeNestedSerializer, PaymentNestedSerializer
)


class FeeCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for FeeCategory model"""
    
    queryset = FeeCategory.objects.all()
    serializer_class = FeeCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'display_order', 'created_at']
    ordering = ['display_order', 'name']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active fee categories"""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FeeStructureViewSet(viewsets.ModelViewSet):
    """ViewSet for FeeStructure model"""
    
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['academic_year', 'grade_level', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['academic_year', 'grade_level', 'created_at']
    ordering = ['academic_year', 'grade_level']
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get fee structure with all its details"""
        fee_structure = self.get_object()
        details = fee_structure.fee_details.all()
        serializer = FeeStructureDetailNestedSerializer(details, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active fee structures"""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_academic_year(self, request):
        """Get fee structures grouped by academic year"""
        academic_year = request.query_params.get('academic_year')
        if not academic_year:
            return Response(
                {"error": "academic_year parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(academic_year=academic_year)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FeeStructureDetailViewSet(viewsets.ModelViewSet):
    """ViewSet for FeeStructureDetail model"""
    
    queryset = FeeStructureDetail.objects.all()
    serializer_class = FeeStructureDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['fee_structure', 'fee_category', 'frequency', 'is_optional']
    search_fields = ['fee_structure__name', 'fee_category__name']
    ordering_fields = ['amount', 'due_date', 'created_at']
    ordering = ['fee_structure__academic_year', 'fee_structure__grade_level', 'fee_category__display_order']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FeeStructureDetailNestedSerializer
        return FeeStructureDetailSerializer


class StudentFeeViewSet(viewsets.ModelViewSet):
    """ViewSet for StudentFee model"""
    
    queryset = StudentFee.objects.all()
    serializer_class = StudentFeeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'academic_year', 'fee_structure_detail__fee_structure__grade_level']
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name',
        'fee_structure_detail__fee_category__name'
    ]
    ordering_fields = ['due_date', 'amount_due', 'amount_paid', 'created_at']
    ordering = ['due_date', 'student__roll_number']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StudentFeeNestedSerializer
        return StudentFeeSerializer
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue fees"""
        queryset = self.get_queryset().filter(
            due_date__lt=timezone.now().date(),
            status='PENDING'
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Get fees for a specific student"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {"error": "student_id parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(student_id=student_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get fee summary statistics"""
        total_students = StudentFee.objects.values('student').distinct().count()
        total_fees_due = StudentFee.objects.aggregate(total=Sum('amount_due'))['total'] or 0
        total_fees_paid = StudentFee.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
        total_balance = total_fees_due - total_fees_paid
        
        overdue_count = StudentFee.objects.filter(
            due_date__lt=timezone.now().date(),
            status='PENDING'
        ).count()
        
        pending_count = StudentFee.objects.filter(status='PENDING').count()
        paid_count = StudentFee.objects.filter(status='PAID').count()
        
        summary_data = {
            'total_students': total_students,
            'total_fees_due': total_fees_due,
            'total_fees_paid': total_fees_paid,
            'total_balance': total_balance,
            'overdue_count': overdue_count,
            'pending_count': pending_count,
            'paid_count': paid_count,
        }
        
        serializer = FeeSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def student_summary(self, request):
        """Get fee summary for all students"""
        student_fees = StudentFee.objects.values('student').annotate(
            total_fees_due=Sum('amount_due'),
            total_fees_paid=Sum('amount_paid'),
            overdue_amount=Sum('late_fee_amount')
        )
        
        summaries = []
        for fee_data in student_fees:
            student = fee_data['student']
            total_balance = fee_data['total_fees_due'] - fee_data['total_fees_paid']
            
            # Get last payment date
            last_payment = Payment.objects.filter(
                student_fee__student=student,
                status='COMPLETED'
            ).order_by('-payment_date').first()
            
            summary = {
                'student_id': student,
                'roll_number': StudentFee.objects.filter(student=student).first().student.roll_number,
                'student_name': f"{StudentFee.objects.filter(student=student).first().student.first_name} {StudentFee.objects.filter(student=student).first().student.last_name}",
                'total_fees_due': fee_data['total_fees_due'],
                'total_fees_paid': fee_data['total_fees_paid'],
                'total_balance': total_balance,
                'overdue_amount': fee_data['overdue_amount'],
                'status': 'PAID' if total_balance <= 0 else 'PENDING',
                'last_payment_date': last_payment.payment_date if last_payment else None
            }
            summaries.append(summary)
        
        serializer = StudentFeeSummarySerializer(summaries, many=True)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment model"""
    
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_method', 'status', 'student_fee__academic_year']
    search_fields = [
        'receipt_number', 'transaction_id', 'reference_number',
        'student_fee__student__roll_number', 'student_fee__student__first_name'
    ]
    ordering_fields = ['payment_date', 'amount', 'created_at']
    ordering = ['-payment_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentNestedSerializer
        return PaymentSerializer
    
    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Get payments within a date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "start_date and end_date parameters are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            payment_date__date__range=[start_date, end_date]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_method(self, request):
        """Get payments by payment method"""
        payment_method = request.query_params.get('method')
        if not payment_method:
            return Response(
                {"error": "method parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(payment_method=payment_method)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark payment as completed"""
        payment = self.get_object()
        payment.status = 'COMPLETED'
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)


class FeeWaiverViewSet(viewsets.ModelViewSet):
    """ViewSet for FeeWaiver model"""
    
    queryset = FeeWaiver.objects.all()
    serializer_class = FeeWaiverSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['waiver_type', 'is_active', 'approved_by']
    search_fields = [
        'student_fee__student__roll_number', 'student_fee__student__first_name',
        'reason'
    ]
    ordering_fields = ['amount', 'approved_date', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active waivers"""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a waiver"""
        waiver = self.get_object()
        waiver.is_active = True
        waiver.approved_by = request.user
        waiver.approved_date = timezone.now()
        waiver.save()
        
        serializer = self.get_serializer(waiver)
        return Response(serializer.data)


class FeeDiscountViewSet(viewsets.ModelViewSet):
    """ViewSet for FeeDiscount model"""
    
    queryset = FeeDiscount.objects.all()
    serializer_class = FeeDiscountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['discount_type', 'is_active']
    search_fields = [
        'student_fee__student__roll_number', 'student_fee__student__first_name',
        'reason'
    ]
    ordering_fields = ['amount', 'valid_until', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active discounts"""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def valid(self, request):
        """Get valid discounts (not expired)"""
        queryset = self.get_queryset().filter(
            Q(is_active=True) & 
            (Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.now().date()))
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FeeReceiptViewSet(viewsets.ModelViewSet):
    """ViewSet for FeeReceipt model"""
    
    queryset = FeeReceipt.objects.all()
    serializer_class = FeeReceiptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_printed', 'generated_by']
    search_fields = [
        'receipt_number', 'student_fee__student__roll_number',
        'student_fee__student__first_name'
    ]
    ordering_fields = ['generated_date', 'printed_date', 'created_at']
    ordering = ['-generated_date']
    
    @action(detail=False, methods=['get'])
    def unprinted(self, request):
        """Get unprinted receipts"""
        queryset = self.get_queryset().filter(is_printed=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_printed(self, request, pk=None):
        """Mark receipt as printed"""
        receipt = self.get_object()
        receipt.is_printed = True
        receipt.printed_date = timezone.now()
        receipt.save()
        
        serializer = self.get_serializer(receipt)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download receipt (placeholder for PDF generation)"""
        receipt = self.get_object()
        # Here you would implement PDF generation logic
        return Response({
            "message": f"Receipt {receipt.receipt_number} download initiated",
            "receipt_number": receipt.receipt_number
        })
