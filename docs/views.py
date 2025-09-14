from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from .models import (
    Category, Tutorial, APIEndpoint, CodeExample, 
    Step, DocumentationPage, FAQ
)


class DocumentationHomeView(ListView):
    """Home page for documentation with categories and featured content"""
    model = Category
    template_name = 'docs/home.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_tutorials'] = Tutorial.objects.filter(
            featured=True, is_published=True
        ).order_by('order', 'title')[:6]
        context['featured_apis'] = APIEndpoint.objects.filter(
            featured=True, is_active=True
        ).order_by('order', 'title')[:6]
        context['recent_tutorials'] = Tutorial.objects.filter(
            is_published=True
        ).order_by('-created_at')[:5]
        return context


class CategoryListView(ListView):
    """List all categories"""
    model = Category
    template_name = 'docs/categories.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('order', 'name')


class CategoryDetailView(DetailView):
    """Show tutorials and APIs for a specific category"""
    model = Category
    template_name = 'docs/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        # Get tutorials and APIs for this category
        tutorials = Tutorial.objects.filter(
            category=category, is_published=True
        ).order_by('order', 'title')
        
        apis = APIEndpoint.objects.filter(
            category=category, is_active=True
        ).order_by('order', 'title')
        
        context['tutorials'] = tutorials
        context['apis'] = apis
        return context


class TutorialListView(ListView):
    """List all tutorials with filtering and search"""
    model = Tutorial
    template_name = 'docs/tutorials.html'
    context_object_name = 'tutorials'
    paginate_by = 12

    def get_queryset(self):
        queryset = Tutorial.objects.filter(is_published=True).order_by('order', 'title')
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by difficulty
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True).order_by('order', 'name')
        context['difficulty_choices'] = Tutorial.DIFFICULTY_CHOICES
        return context


class TutorialDetailView(DetailView):
    """Show tutorial details with steps and code examples"""
    model = Tutorial
    template_name = 'docs/tutorial_detail.html'
    context_object_name = 'tutorial'

    def get_queryset(self):
        return Tutorial.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutorial = self.get_object()
        
        # Get steps and code examples
        context['steps'] = tutorial.steps.all().order_by('order')
        context['code_examples'] = tutorial.code_examples.all().order_by('order')
        
        # Get related tutorials
        context['related_tutorials'] = Tutorial.objects.filter(
            category=tutorial.category,
            is_published=True
        ).exclude(id=tutorial.id).order_by('order', 'title')[:4]
        
        # Increment view count
        Tutorial.objects.filter(id=tutorial.id).update(view_count=F('view_count') + 1)
        
        return context


class APIListView(ListView):
    """List all API endpoints with filtering and search"""
    model = APIEndpoint
    template_name = 'docs/apis.html'
    context_object_name = 'apis'
    paginate_by = 12

    def get_queryset(self):
        queryset = APIEndpoint.objects.filter(is_active=True).order_by('order', 'title')
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by method
        method = self.request.GET.get('method')
        if method:
            queryset = queryset.filter(method=method)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(endpoint__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True).order_by('order', 'name')
        context['method_choices'] = APIEndpoint.METHOD_CHOICES
        return context


class APIDetailView(DetailView):
    """Show API endpoint details with examples"""
    model = APIEndpoint
    template_name = 'docs/api_detail.html'
    context_object_name = 'api'

    def get_queryset(self):
        return APIEndpoint.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api = self.get_object()
        
        # Get code examples
        context['code_examples'] = api.code_examples.all().order_by('order')
        
        # Get related APIs
        context['related_apis'] = APIEndpoint.objects.filter(
            category=api.category,
            is_active=True
        ).exclude(id=api.id).order_by('order', 'title')[:4]
        
        return context


class DocumentationPageView(DetailView):
    """Show static documentation pages"""
    model = DocumentationPage
    template_name = 'docs/page.html'
    context_object_name = 'page'

    def get_queryset(self):
        return DocumentationPage.objects.filter(is_published=True)


class FAQListView(ListView):
    """List all FAQs"""
    model = FAQ
    template_name = 'docs/faq.html'
    context_object_name = 'faqs'

    def get_queryset(self):
        return FAQ.objects.filter(is_published=True).order_by('order', 'question')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True).order_by('order', 'name')
        return context


def search_view(request):
    """Global search across tutorials and APIs"""
    query = request.GET.get('q', '')
    results = {
        'tutorials': [],
        'apis': [],
        'pages': [],
    }
    
    if query:
        # Search tutorials
        results['tutorials'] = Tutorial.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__icontains=query),
            is_published=True
        ).order_by('order', 'title')[:10]
        
        # Search APIs
        results['apis'] = APIEndpoint.objects.filter(
            Q(title__icontains=query) |
            Q(endpoint__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query),
            is_active=True
        ).order_by('order', 'title')[:10]
        
        # Search pages
        results['pages'] = DocumentationPage.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query),
            is_published=True
        ).order_by('order', 'title')[:10]
    
    return render(request, 'docs/search.html', {
        'query': query,
        'results': results,
    })


def api_json_view(request):
    """JSON API for frontend integration"""
    endpoint_type = request.GET.get('type', 'all')
    
    if endpoint_type == 'tutorials':
        tutorials = Tutorial.objects.filter(is_published=True).order_by('order', 'title')
        data = []
        for tutorial in tutorials:
            data.append({
                'id': tutorial.id,
                'title': tutorial.title,
                'slug': tutorial.slug,
                'description': tutorial.description,
                'category': tutorial.category.name,
                'difficulty': tutorial.difficulty,
                'estimated_time': tutorial.estimated_time,
                'tags': tutorial.get_tags_list(),
                'url': f'/docs/tutorials/{tutorial.slug}/',
            })
        return JsonResponse({'tutorials': data})
    
    elif endpoint_type == 'apis':
        apis = APIEndpoint.objects.filter(is_active=True).order_by('order', 'title')
        data = []
        for api in apis:
            data.append({
                'id': api.id,
                'title': api.title,
                'endpoint': api.endpoint,
                'method': api.method,
                'description': api.description,
                'category': api.category.name,
                'authentication_required': api.authentication_required,
                'tags': api.get_tags_list(),
                'url': f'/docs/apis/{api.id}/',
            })
        return JsonResponse({'apis': data})
    
    elif endpoint_type == 'categories':
        categories = Category.objects.filter(is_active=True).order_by('order', 'name')
        data = []
        for category in categories:
            data.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'icon': category.icon,
                'color': category.color,
                'url': f'/docs/categories/{category.slug}/',
            })
        return JsonResponse({'categories': data})
    
    else:
        # Return all data
        return JsonResponse({
            'tutorials': list(Tutorial.objects.filter(is_published=True).values(
                'id', 'title', 'slug', 'description', 'difficulty', 'estimated_time'
            )),
            'apis': list(APIEndpoint.objects.filter(is_active=True).values(
                'id', 'title', 'endpoint', 'method', 'description', 'authentication_required'
            )),
            'categories': list(Category.objects.filter(is_active=True).values(
                'id', 'name', 'slug', 'description', 'icon', 'color'
            )),
        })