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
    
    # Assignments
    path('', views.AssignmentListCreateView.as_view(), name='assignment-list-create'),
    path('<uuid:pk>/', views.AssignmentDetailView.as_view(), name='assignment-detail'),
    path('my-assignments/', views.my_assignments, name='my-assignments'),
    path('<uuid:assignment_id>/publish/', views.publish_assignment, name='publish-assignment'),
    path('<uuid:assignment_id>/close/', views.close_assignment, name='close-assignment'),
    path('<uuid:assignment_id>/submissions/', views.assignment_submissions, name='assignment-submissions'),
    
    # Assignment Submissions
    path('<uuid:assignment_id>/submit/', views.AssignmentSubmissionListCreateView.as_view(), name='submission-list-create'),
    path('submissions/<uuid:pk>/', views.AssignmentSubmissionDetailView.as_view(), name='submission-detail'),
    
    # Assignment Grades
    path('submissions/<uuid:submission_id>/grade/', views.AssignmentGradeCreateUpdateView.as_view(), name='grade-create-update'),
    
    # Assignment Comments
    path('<uuid:assignment_id>/comments/', views.AssignmentCommentListCreateView.as_view(), name='comment-list-create'),
    
    # File Upload
    path('files/upload/', views.AssignmentFileUploadView.as_view(), name='file-upload'),
    
    # Statistics
    path('stats/', views.assignment_stats, name='assignment-stats'),
    
    # Include router URLs
    path('', include(router.urls)),
]
