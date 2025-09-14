from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import FeedbackCategory, FeedbackTag, Feedback, FeedbackComment, FeedbackAttachment, FeedbackVote
from .serializers import (
	FeedbackCategorySerializer,
	FeedbackTagSerializer,
	FeedbackSerializer,
	FeedbackCommentSerializer,
	FeedbackAttachmentSerializer,
	FeedbackVoteSerializer,
)


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
	pass


class FeedbackCategoryViewSet(viewsets.ModelViewSet):
	queryset = FeedbackCategory.objects.all()
	serializer_class = FeedbackCategorySerializer
	permission_classes = [permissions.IsAdminUser]
	filter_backends = [filters.SearchFilter]
	search_fields = ['name']


class FeedbackTagViewSet(viewsets.ModelViewSet):
	queryset = FeedbackTag.objects.all()
	serializer_class = FeedbackTagSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [filters.SearchFilter]
	search_fields = ['name']


class FeedbackViewSet(viewsets.ModelViewSet):
	queryset = Feedback.objects.select_related('category', 'created_by').prefetch_related('tags').all()
	serializer_class = FeedbackSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
	filterset_fields = [
		'status', 'priority', 'category', 'created_by',
		'department', 'course', 'section', 'faculty', 'syllabus',
		'target_type', 'target_id'
	]
	search_fields = ['title', 'description']
	ordering_fields = ['created_at', 'updated_at', 'priority']

	def perform_create(self, serializer):
		serializer.save()


class FeedbackCommentViewSet(viewsets.ModelViewSet):
	queryset = FeedbackComment.objects.select_related('feedback', 'commented_by').all()
	serializer_class = FeedbackCommentSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ['feedback', 'commented_by', 'is_internal']

	def perform_create(self, serializer):
		serializer.save()


class FeedbackAttachmentViewSet(viewsets.ModelViewSet):
	queryset = FeedbackAttachment.objects.select_related('feedback', 'uploaded_by').all()
	serializer_class = FeedbackAttachmentSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ['feedback', 'uploaded_by']

	def perform_create(self, serializer):
		serializer.save()


class FeedbackVoteViewSet(viewsets.ModelViewSet):
	queryset = FeedbackVote.objects.select_related('feedback', 'voted_by').all()
	serializer_class = FeedbackVoteSerializer
	permission_classes = [permissions.IsAuthenticated]
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ['feedback', 'voted_by', 'is_upvote']

	def perform_create(self, serializer):
		serializer.save()
