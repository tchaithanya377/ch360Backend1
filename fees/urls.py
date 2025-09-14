from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.FeeCategoryViewSet)
router.register(r'structures', views.FeeStructureViewSet)
router.register(r'structure-details', views.FeeStructureDetailViewSet)
router.register(r'student-fees', views.StudentFeeViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'waivers', views.FeeWaiverViewSet)
router.register(r'discounts', views.FeeDiscountViewSet)
router.register(r'receipts', views.FeeReceiptViewSet)

app_name = 'fees'

urlpatterns = [
    path('api/', include(router.urls)),
]
