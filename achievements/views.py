from django.shortcuts import render
from rest_framework import viewsets
from core.viewsets import HighPerformanceViewSet
from .models import Achievement, Skill, Education, Experience, Publication, Project, ResumeProfile
from .serializers import (
	AchievementSerializer, SkillSerializer, EducationSerializer,
	ExperienceSerializer, PublicationSerializer, ProjectSerializer,
	ResumeProfileSerializer
)


class AchievementViewSet(HighPerformanceViewSet):
	queryset = Achievement.objects.all().select_related('owner_content_type')
	serializer_class = AchievementSerializer
	filterset_fields = ['category', 'owner_type', 'is_public']
	search_fields = ['title', 'description', 'issuer_or_organizer', 'location']
	ordering_fields = ['achieved_on', 'created_at', 'updated_at']


class SkillViewSet(HighPerformanceViewSet):
	queryset = Skill.objects.all().select_related('owner_content_type')
	serializer_class = SkillSerializer
	filterset_fields = ['owner_type', 'is_core']
	search_fields = ['name']
	ordering_fields = ['proficiency', 'name', 'updated_at']


class EducationViewSet(HighPerformanceViewSet):
	queryset = Education.objects.all().select_related('owner_content_type')
	serializer_class = EducationSerializer
	filterset_fields = ['owner_type']
	search_fields = ['institution', 'degree', 'field_of_study']
	ordering_fields = ['start_date', 'end_date', 'updated_at']


class ExperienceViewSet(HighPerformanceViewSet):
	queryset = Experience.objects.all().select_related('owner_content_type')
	serializer_class = ExperienceSerializer
	filterset_fields = ['owner_type', 'currently_working']
	search_fields = ['title', 'organization', 'location']
	ordering_fields = ['start_date', 'end_date', 'updated_at']


class PublicationViewSet(HighPerformanceViewSet):
	queryset = Publication.objects.all().select_related('owner_content_type')
	serializer_class = PublicationSerializer
	filterset_fields = ['owner_type', 'year']
	search_fields = ['title', 'authors', 'journal_or_conference', 'doi']
	ordering_fields = ['year', 'updated_at']


class ProjectViewSet(HighPerformanceViewSet):
	queryset = Project.objects.all().select_related('owner_content_type')
	serializer_class = ProjectSerializer
	filterset_fields = ['owner_type']
	search_fields = ['title', 'description', 'role']
	ordering_fields = ['start_date', 'end_date', 'updated_at']


class ResumeProfileViewSet(HighPerformanceViewSet):
	queryset = ResumeProfile.objects.all().select_related('owner_content_type')
	serializer_class = ResumeProfileSerializer
	filterset_fields = ['owner_type']
	search_fields = ['headline', 'summary', 'location']
	ordering_fields = ['updated_at', 'created_at']
