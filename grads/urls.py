from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'grads'

router = DefaultRouter()
router.register(r'grade-scales', views.GradeScaleViewSet)
router.register(r'midterm-grades', views.MidTermGradeViewSet)
router.register(r'semester-grades', views.SemesterGradeViewSet)
router.register(r'semester-gpas', views.SemesterGPAViewSet)
router.register(r'cumulative-gpas', views.CumulativeGPAViewSet)

urlpatterns = [
    path('health/', views.health, name='grads_health'),
    path('', include(router.urls)),
]