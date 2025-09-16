from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for viewsets (if any)
router = DefaultRouter()

app_name = 'assignments'

urlpatterns = [
    # Assignment Categories
    path('categories/', views.AssignmentCategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<uuid:pk>/', views.AssignmentCategoryDetailView.as_view(), name='category-detail'),
    
    # Assignment Templates
    path('templates/', views.AssignmentTemplateListCreateView.as_view(), name='template-list-create'),
    path('templates/<uuid:pk>/', views.AssignmentTemplateDetailView.as_view(), name='template-detail'),
    
    # Assignment Rubrics
    path('rubrics/', views.AssignmentRubricListCreateView.as_view(), name='rubric-list-create'),
    path('rubrics/<uuid:pk>/', views.AssignmentRubricDetailView.as_view(), name='rubric-detail'),
    
    # Assignments
    path('', views.AssignmentListCreateView.as_view(), name='assignment-list-create'),
    path('<uuid:pk>/', views.AssignmentDetailView.as_view(), name='assignment-detail'),
    # Simple endpoints
    path('simple/', views.SimpleAssignmentListCreateView.as_view(), name='simple-assignment-list-create'),
    path('simple/<uuid:pk>/', views.SimpleAssignmentDetailView.as_view(), name='simple-assignment-detail'),
    path('my-assignments/', views.my_assignments, name='my-assignments'),
    path('<uuid:assignment_id>/publish/', views.publish_assignment, name='publish-assignment'),
    path('<uuid:assignment_id>/close/', views.close_assignment, name='close-assignment'),
    path('<uuid:assignment_id>/submissions/', views.assignment_submissions, name='assignment-submissions'),
    path('<uuid:assignment_id>/analytics/', views.assignment_analytics_dashboard, name='assignment-analytics-dashboard'),
    path('<uuid:assignment_id>/auto-groups/', views.auto_create_groups_from_batch, name='assignment-auto-groups'),
    path('<uuid:assignment_id>/assign-section/', views.assign_assignment_to_section, name='assignment-assign-section'),
    
    # Assignment Submissions
    path('<uuid:assignment_id>/submit/', views.AssignmentSubmissionListCreateView.as_view(), name='submission-list-create'),
    path('submissions/<uuid:pk>/', views.AssignmentSubmissionDetailView.as_view(), name='submission-detail'),
    
    # Assignment Grades
    path('submissions/<uuid:submission_id>/grade/', views.AssignmentGradeCreateUpdateView.as_view(), name='grade-create-update'),
    path('submissions/<uuid:submission_id>/rubric-grade/', views.AssignmentRubricGradeCreateUpdateView.as_view(), name='rubric-grade-create-update'),
    
    # Assignment Comments
    path('<uuid:assignment_id>/comments/', views.AssignmentCommentListCreateView.as_view(), name='comment-list-create'),
    
    # Learning Outcomes
    path('<uuid:assignment_id>/learning-outcomes/', views.AssignmentLearningOutcomeListCreateView.as_view(), name='learning-outcome-list-create'),
    
    # Peer Reviews
    path('<uuid:assignment_id>/peer-reviews/', views.AssignmentPeerReviewListCreateView.as_view(), name='peer-review-list-create'),
    path('<uuid:assignment_id>/assign-peer-reviews/', views.assign_peer_reviews, name='assign-peer-reviews'),
    
    # Plagiarism Checks
    path('<uuid:assignment_id>/plagiarism-checks/', views.AssignmentPlagiarismCheckListCreateView.as_view(), name='plagiarism-check-list-create'),
    path('submissions/<uuid:submission_id>/run-plagiarism-check/', views.run_plagiarism_check, name='run-plagiarism-check'),
    
    # Notifications
    path('notifications/', views.AssignmentNotificationListCreateView.as_view(), name='notification-list-create'),
    path('notifications/<uuid:pk>/', views.AssignmentNotificationDetailView.as_view(), name='notification-detail'),
    
    # Schedules
    path('schedules/', views.AssignmentScheduleListCreateView.as_view(), name='schedule-list-create'),
    
    # File Upload
    path('files/upload/', views.AssignmentFileUploadView.as_view(), name='file-upload'),
    
    # Statistics
    path('stats/', views.assignment_stats, name='assignment-stats'),
    
    # Include router URLs
    path('', include(router.urls)),
]
