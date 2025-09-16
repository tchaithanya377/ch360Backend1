from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MentorshipViewSet, ProjectViewSet, MeetingViewSet, FeedbackViewSet, ActionItemViewSet

app_name = 'mentoring'

router = DefaultRouter()
router.register(r'mentorships', MentorshipViewSet, basename='mentorship')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'meetings', MeetingViewSet, basename='meeting')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'action-items', ActionItemViewSet, basename='actionitem')

urlpatterns = [
    path('', include(router.urls)),
]


