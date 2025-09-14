from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'facilities'

# API router for REST endpoints (temporarily disabled to fix routing)
# router = DefaultRouter()
# router.register(r'buildings', views.BuildingViewSet, basename='api_building')
# router.register(r'rooms', views.RoomViewSet, basename='api_room')
# router.register(r'equipment', views.EquipmentViewSet, basename='api_equipment')
# router.register(r'bookings', views.BookingViewSet, basename='api_booking')
# router.register(r'maintenance', views.MaintenanceViewSet, basename='api_maintenance')

urlpatterns = [
    # Dashboard views (must come first to avoid conflicts with API routes)
    path('', views.facilities_dashboard, name='dashboard'),
    path('buildings/', views.buildings_list, name='buildings_list'),
    path('buildings/<int:building_id>/', views.building_detail, name='building_detail'),
    path('rooms/', views.rooms_list, name='rooms_list'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('bookings/', views.bookings_list, name='bookings_list'),
    path('bookings/create/', views.booking_create, name='booking_create'),
    path('bookings/<int:booking_id>/approve/', views.booking_approve, name='booking_approve'),
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('rooms/<int:room_id>/availability/', views.api_room_availability, name='room_availability'),
    
    # API endpoints (temporarily disabled to fix routing)
    # path('api/v1/', include(router.urls)),
]
