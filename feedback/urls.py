from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
	FeedbackCategoryViewSet,
	FeedbackTagViewSet,
	FeedbackViewSet,
	FeedbackCommentViewSet,
	FeedbackAttachmentViewSet,
	FeedbackVoteViewSet,
)

app_name = 'feedback'

router = DefaultRouter()
router.register(r'categories', FeedbackCategoryViewSet, basename='feedback-category')
router.register(r'tags', FeedbackTagViewSet, basename='feedback-tag')
router.register(r'items', FeedbackViewSet, basename='feedback')
router.register(r'comments', FeedbackCommentViewSet, basename='feedback-comment')
router.register(r'attachments', FeedbackAttachmentViewSet, basename='feedback-attachment')
router.register(r'votes', FeedbackVoteViewSet, basename='feedback-vote')

urlpatterns = [
	path('', include(router.urls)),
]
