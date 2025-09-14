from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Category(models.Model):
    """Categories for organizing tutorials and API documentation"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    color = models.CharField(max_length=7, default="#007bff", help_text="Hex color code")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Tutorial(models.Model):
    """Tutorial articles with step-by-step instructions"""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    content = models.TextField(help_text="Markdown content")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='tutorials')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    estimated_time = models.PositiveIntegerField(help_text="Estimated time in minutes")
    prerequisites = models.TextField(blank=True, help_text="What you need to know before starting")
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def get_tags_list(self):
        """Return tags as a list"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class APIEndpoint(models.Model):
    """API endpoint documentation"""
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]

    title = models.CharField(max_length=200)
    endpoint = models.CharField(max_length=500, help_text="API endpoint URL")
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='api_endpoints')
    
    # Request details
    request_headers = models.JSONField(default=dict, blank=True, help_text="Required headers")
    request_body = models.JSONField(default=dict, blank=True, help_text="Request body schema")
    query_parameters = models.JSONField(default=dict, blank=True, help_text="Query parameters")
    path_parameters = models.JSONField(default=dict, blank=True, help_text="Path parameters")
    
    # Response details
    response_schema = models.JSONField(default=dict, blank=True, help_text="Response schema")
    example_response = models.JSONField(default=dict, blank=True, help_text="Example response")
    status_codes = models.JSONField(default=dict, blank=True, help_text="Possible status codes")
    
    # Additional info
    authentication_required = models.BooleanField(default=False)
    rate_limit = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']
        unique_together = ['endpoint', 'method']

    def __str__(self):
        return f"{self.method} {self.endpoint}"

    def get_tags_list(self):
        """Return tags as a list"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class CodeExample(models.Model):
    """Code examples for tutorials and API endpoints"""
    LANGUAGE_CHOICES = [
        ('javascript', 'JavaScript'),
        ('python', 'Python'),
        ('curl', 'cURL'),
        ('json', 'JSON'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('sql', 'SQL'),
        ('bash', 'Bash'),
        ('php', 'PHP'),
        ('java', 'Java'),
        ('csharp', 'C#'),
        ('go', 'Go'),
        ('rust', 'Rust'),
    ]

    title = models.CharField(max_length=200)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    code = models.TextField()
    description = models.TextField(blank=True)
    tutorial = models.ForeignKey(Tutorial, on_delete=models.CASCADE, related_name='code_examples', null=True, blank=True)
    api_endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE, related_name='code_examples', null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return f"{self.title} ({self.language})"


class Step(models.Model):
    """Step-by-step instructions for tutorials"""
    tutorial = models.ForeignKey(Tutorial, on_delete=models.CASCADE, related_name='steps')
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Markdown content")
    order = models.PositiveIntegerField()
    has_code = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ['tutorial', 'order']

    def __str__(self):
        return f"{self.tutorial.title} - Step {self.order}: {self.title}"


class DocumentationPage(models.Model):
    """Static documentation pages"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField(help_text="Markdown content")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='pages', null=True, blank=True)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class FAQ(models.Model):
    """Frequently Asked Questions"""
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='faqs', null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question