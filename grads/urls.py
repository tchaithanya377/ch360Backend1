from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'grads'

router = DefaultRouter()
router.register(r'grade-scales', views.GradeScaleViewSet, basename='grade-scale')
router.register(r'terms', views.TermViewSet, basename='term')
router.register(r'course-results', views.CourseResultViewSet, basename='course-result')
router.register(r'term-gpa', views.TermGPAViewSet, basename='term-gpa')
router.register(r'graduates', views.GraduateRecordViewSet, basename='graduate')

urlpatterns = [
    path('health/', views.health, name='health'),
    path('', include(router.urls)),
]


