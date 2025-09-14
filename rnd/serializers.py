from rest_framework import serializers
from django.contrib.auth import get_user_model
from . import models

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        ref_name = 'RNDUser'


class ResearcherSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    
    class Meta:
        model = models.Researcher
        fields = '__all__'


class GrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Grant
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    principal_investigator = ResearcherSerializer(read_only=True)
    principal_investigator_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Researcher.objects.all(),
        source='principal_investigator',
        write_only=True
    )
    members = ResearcherSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=models.Researcher.objects.all(),
        source='members',
        write_only=True,
        many=True,
        required=False
    )
    grants = GrantSerializer(many=True, read_only=True)
    grant_ids = serializers.PrimaryKeyRelatedField(
        queryset=models.Grant.objects.all(),
        source='grants',
        write_only=True,
        many=True,
        required=False
    )
    
    class Meta:
        model = models.Project
        fields = '__all__'


class PublicationSerializer(serializers.ModelSerializer):
    authors = ResearcherSerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=models.Researcher.objects.all(),
        source='authors',
        write_only=True,
        many=True,
        required=False
    )
    projects = ProjectSerializer(many=True, read_only=True)
    project_ids = serializers.PrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
        source='projects',
        write_only=True,
        many=True,
        required=False
    )
    
    class Meta:
        model = models.Publication
        fields = '__all__'


class PatentSerializer(serializers.ModelSerializer):
    inventors = ResearcherSerializer(many=True, read_only=True)
    inventor_ids = serializers.PrimaryKeyRelatedField(
        queryset=models.Researcher.objects.all(),
        source='inventors',
        write_only=True,
        many=True,
        required=False
    )
    projects = ProjectSerializer(many=True, read_only=True)
    project_ids = serializers.PrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
        source='projects',
        write_only=True,
        many=True,
        required=False
    )
    
    class Meta:
        model = models.Patent
        fields = '__all__'


class DatasetSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True, read_only=True)
    project_ids = serializers.PrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
        source='projects',
        write_only=True,
        many=True,
        required=False
    )
    
    class Meta:
        model = models.Dataset
        fields = '__all__'


class CollaborationSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Project.objects.all(),
        source='project',
        write_only=True
    )
    
    class Meta:
        model = models.Collaboration
        fields = '__all__'


# Detail Serializers for Nested Data
class ProjectDetailSerializer(ProjectSerializer):
    publications = PublicationSerializer(many=True, read_only=True)
    patents = PatentSerializer(many=True, read_only=True)
    datasets = DatasetSerializer(many=True, read_only=True)
    collaborations = CollaborationSerializer(many=True, read_only=True)


class ResearcherDetailSerializer(ResearcherSerializer):
    led_projects = ProjectSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    publications = PublicationSerializer(many=True, read_only=True)
    patents = PatentSerializer(many=True, read_only=True)


# Statistics Serializers
class RDStatsSerializer(serializers.Serializer):
    total_researchers = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    total_grants = serializers.IntegerField()
    total_publications = serializers.IntegerField()
    total_patents = serializers.IntegerField()
    total_datasets = serializers.IntegerField()
    total_collaborations = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    total_grant_amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class ProjectStatsSerializer(serializers.Serializer):
    project = ProjectSerializer()
    publications_count = serializers.IntegerField()
    patents_count = serializers.IntegerField()
    datasets_count = serializers.IntegerField()
    collaborations_count = serializers.IntegerField()
    total_grant_amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class ResearcherStatsSerializer(serializers.Serializer):
    researcher = ResearcherSerializer()
    led_projects_count = serializers.IntegerField()
    publications_count = serializers.IntegerField()
    patents_count = serializers.IntegerField()
    total_citations = serializers.IntegerField()


# Search and Filter Serializers
class SearchFilterSerializer(serializers.Serializer):
    query = serializers.CharField(required=False)
    model_type = serializers.ChoiceField(
        choices=[
            ('researcher', 'Researcher'),
            ('project', 'Project'),
            ('publication', 'Publication'),
            ('patent', 'Patent'),
            ('dataset', 'Dataset'),
            ('collaboration', 'Collaboration')
        ],
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    status = serializers.CharField(required=False)
    department = serializers.CharField(required=False)


# Bulk Operations Serializers
class BulkCreateSerializer(serializers.Serializer):
    model_type = serializers.ChoiceField(
        choices=[
            ('researcher', 'Researcher'),
            ('project', 'Project'),
            ('publication', 'Publication'),
            ('patent', 'Patent'),
            ('dataset', 'Dataset'),
            ('collaboration', 'Collaboration')
        ]
    )
    data = serializers.ListField(child=serializers.DictField())


class BulkUpdateSerializer(serializers.Serializer):
    model_type = serializers.ChoiceField(
        choices=[
            ('researcher', 'Researcher'),
            ('project', 'Project'),
            ('publication', 'Publication'),
            ('patent', 'Patent'),
            ('dataset', 'Dataset'),
            ('collaboration', 'Collaboration')
        ]
    )
    ids = serializers.ListField(child=serializers.IntegerField())
    updates = serializers.DictField()


class BulkDeleteSerializer(serializers.Serializer):
    model_type = serializers.ChoiceField(
        choices=[
            ('researcher', 'Researcher'),
            ('project', 'Project'),
            ('publication', 'Publication'),
            ('patent', 'Patent'),
            ('dataset', 'Dataset'),
            ('collaboration', 'Collaboration')
        ]
    )
    ids = serializers.ListField(child=serializers.IntegerField())


# Import/Export Serializers
class ImportExportSerializer(serializers.Serializer):
    model_type = serializers.ChoiceField(
        choices=[
            ('researcher', 'Researcher'),
            ('project', 'Project'),
            ('publication', 'Publication'),
            ('patent', 'Patent'),
            ('dataset', 'Dataset'),
            ('collaboration', 'Collaboration')
        ]
    )
    format = serializers.ChoiceField(choices=[('csv', 'CSV'), ('json', 'JSON'), ('xlsx', 'Excel')])
    file = serializers.FileField(required=False)
    include_related = serializers.BooleanField(default=False)


# Alert Serializers
class AlertSerializer(serializers.Serializer):
    alert_type = serializers.ChoiceField(
        choices=[
            ('deadline', 'Deadline Approaching'),
            ('overdue', 'Overdue'),
            ('milestone', 'Milestone Due'),
            ('budget', 'Budget Alert'),
            ('publication', 'Publication Due'),
            ('report', 'Report Due')
        ]
    )
    title = serializers.CharField()
    message = serializers.CharField()
    severity = serializers.ChoiceField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    related_object_type = serializers.CharField()
    related_object_id = serializers.IntegerField()
    due_date = serializers.DateTimeField(required=False)


# Dashboard Widget Serializers
class DashboardWidgetSerializer(serializers.Serializer):
    widget_type = serializers.ChoiceField(
        choices=[
            ('stats', 'Statistics'),
            ('chart', 'Chart'),
            ('table', 'Table'),
            ('progress', 'Progress Bar'),
            ('calendar', 'Calendar'),
            ('alerts', 'Alerts')
        ]
    )
    title = serializers.CharField()
    data = serializers.DictField()
    position = serializers.IntegerField()
    size = serializers.ChoiceField(choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')])
    refresh_interval = serializers.IntegerField(required=False)


