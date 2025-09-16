from rest_framework.routers import DefaultRouter
from .views import (
	AchievementViewSet, SkillViewSet, EducationViewSet, ExperienceViewSet,
	PublicationViewSet, ProjectViewSet, ResumeProfileViewSet
)

router = DefaultRouter()
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'education', EducationViewSet, basename='education')
router.register(r'experiences', ExperienceViewSet, basename='experience')
router.register(r'publications', PublicationViewSet, basename='publication')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'resume-profiles', ResumeProfileViewSet, basename='resume-profile')

urlpatterns = router.urls
