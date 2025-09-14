from django.contrib import admin
from .models import FeedbackCategory, FeedbackTag, Feedback, FeedbackComment, FeedbackAttachment, FeedbackVote


@admin.register(FeedbackCategory)
class FeedbackCategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'is_active', 'created_at')
	search_fields = ('name',)
	list_filter = ('is_active',)


@admin.register(FeedbackTag)
class FeedbackTagAdmin(admin.ModelAdmin):
	list_display = ('name', 'created_at')
	search_fields = ('name',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'status', 'priority', 'created_by', 'created_at')
	list_filter = ('status', 'priority', 'category', 'created_at')
	search_fields = ('title', 'description')
	autocomplete_fields = ('category', 'created_by', 'tags')
	filter_horizontal = ('tags',)


@admin.register(FeedbackComment)
class FeedbackCommentAdmin(admin.ModelAdmin):
	list_display = ('feedback', 'commented_by', 'is_internal', 'created_at')
	list_filter = ('is_internal', 'created_at')
	search_fields = ('content',)


@admin.register(FeedbackAttachment)
class FeedbackAttachmentAdmin(admin.ModelAdmin):
	list_display = ('feedback', 'uploaded_by', 'file_url', 'created_at')
	search_fields = ('file_url', 'description')


@admin.register(FeedbackVote)
class FeedbackVoteAdmin(admin.ModelAdmin):
	list_display = ('feedback', 'voted_by', 'is_upvote', 'created_at')
	list_filter = ('is_upvote',)
