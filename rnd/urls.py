from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


app_name = 'rnd'

router = DefaultRouter()
router.register(r'researchers', views.ResearcherViewSet)
router.register(r'grants', views.GrantViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'publications', views.PublicationViewSet)
router.register(r'patents', views.PatentViewSet)
router.register(r'datasets', views.DatasetViewSet)
router.register(r'collaborations', views.CollaborationViewSet)


urlpatterns = [
    path('', include(router.urls)),
]


