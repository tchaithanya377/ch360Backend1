from django.urls import path
from . import views

app_name = 'docs'

urlpatterns = [
    # Home page
    path('', views.DocumentationHomeView.as_view(), name='home'),
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Tutorials
    path('tutorials/', views.TutorialListView.as_view(), name='tutorials'),
    path('tutorials/<slug:slug>/', views.TutorialDetailView.as_view(), name='tutorial_detail'),
    
    # API Documentation
    path('apis/', views.APIListView.as_view(), name='apis'),
    path('apis/<int:pk>/', views.APIDetailView.as_view(), name='api_detail'),
    
    # Static pages
    path('pages/<slug:slug>/', views.DocumentationPageView.as_view(), name='page'),
    
    # FAQ
    path('faq/', views.FAQListView.as_view(), name='faq'),
    
    # Search
    path('search/', views.search_view, name='search'),
    
    # JSON API for frontend
    path('api/json/', views.api_json_view, name='api_json'),
]
