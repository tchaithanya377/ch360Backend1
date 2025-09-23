from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'course-sections', views.CourseSectionViewSet, basename='course-section')
router.register(r'syllabi', views.SyllabusViewSet, basename='syllabus')
router.register(r'syllabus-topics', views.SyllabusTopicViewSet, basename='syllabus-topic')
router.register(r'timetables', views.TimetableViewSet, basename='timetable')
router.register(r'academic-timetable-slots', views.AcademicTimetableSlotViewSet, basename='academic-timetable-slot')
router.register(r'enrollments', views.CourseEnrollmentViewSet, basename='enrollment')
router.register(r'batch-enrollments', views.BatchCourseEnrollmentViewSet, basename='batch-enrollment')
router.register(r'course-prerequisites', views.CoursePrerequisiteViewSet, basename='course-prerequisite')
router.register(r'academic-calendar', views.AcademicCalendarViewSet, basename='academic-calendar')

app_name = 'academics'

urlpatterns = [
    path('api/', include(router.urls)),
]
