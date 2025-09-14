from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Building, Room, Equipment, RoomEquipment, Booking, Maintenance
from .serializers import (
    BuildingSerializer,
    RoomSerializer,
    EquipmentSerializer,
    RoomEquipmentSerializer,
    BookingSerializer,
    MaintenanceSerializer,
)


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    pass


class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related("building").all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["building", "room_type", "capacity", "is_active"]
    search_fields = ["name", "code", "building__name", "building__code"]
    ordering_fields = ["capacity", "code", "name"]

    @action(detail=True, methods=["get"], url_path="availability")
    def availability(self, request, pk=None):
        room = self.get_object()
        start_param = request.query_params.get("start")
        end_param = request.query_params.get("end")
        try:
            start = timezone.datetime.fromisoformat(start_param) if start_param else timezone.now()
            end = timezone.datetime.fromisoformat(end_param) if end_param else start + timedelta(days=7)
        except ValueError:
            return Response({"detail": "Invalid datetime format"}, status=status.HTTP_400_BAD_REQUEST)

        bookings = room.bookings.filter(starts_at__lt=end, ends_at__gt=start).order_by("starts_at")
        data = BookingSerializer(bookings, many=True).data
        return Response({"room": room.id, "busy": data})


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related("room").all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["room", "is_approved", "created_by"]
    search_fields = ["title", "purpose", "room__code", "room__name"]
    ordering_fields = ["starts_at", "ends_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="conflicts")
    def conflicts(self, request):
        room_id = request.query_params.get("room")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if not (room_id and start and end):
            return Response({"detail": "room, start, end are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            start_dt = timezone.datetime.fromisoformat(start)
            end_dt = timezone.datetime.fromisoformat(end)
        except ValueError:
            return Response({"detail": "Invalid datetime format"}, status=status.HTTP_400_BAD_REQUEST)
        conflicts_qs = Booking.objects.filter(room_id=room_id, starts_at__lt=end_dt, ends_at__gt=start_dt)
        return Response(BookingSerializer(conflicts_qs, many=True).data)


class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.select_related("room").all()
    serializer_class = MaintenanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "room"]
    search_fields = ["title", "description", "room__code", "room__name"]
    ordering_fields = ["scheduled_for", "status"]


# Dashboard Views
@login_required
def facilities_dashboard(request):
    """Main facilities dashboard"""
    context = {
        'total_buildings': Building.objects.count(),
        'total_rooms': Room.objects.count(),
        'total_bookings': Booking.objects.count(),
        'pending_bookings': Booking.objects.filter(is_approved=False).count(),
        'active_maintenance': Maintenance.objects.filter(status='in_progress').count(),
        'recent_bookings': Booking.objects.select_related('room', 'created_by').order_by('-created_at')[:5],
        'upcoming_maintenance': Maintenance.objects.select_related('room').filter(
            status='scheduled', scheduled_for__gte=timezone.now()
        ).order_by('scheduled_for')[:5],
    }
    return render(request, 'facilities/dashboard.html', context)


@login_required
def buildings_list(request):
    """List all buildings"""
    buildings = Building.objects.all()
    return render(request, 'facilities/buildings_list.html', {'buildings': buildings})


@login_required
def building_detail(request, building_id):
    """Building detail with rooms"""
    building = get_object_or_404(Building, id=building_id)
    rooms = building.rooms.all()
    return render(request, 'facilities/building_detail.html', {
        'building': building,
        'rooms': rooms
    })


@login_required
def rooms_list(request):
    """List all rooms with filters"""
    rooms = Room.objects.select_related('building').all()
    
    # Apply filters
    building_filter = request.GET.get('building')
    room_type_filter = request.GET.get('room_type')
    capacity_filter = request.GET.get('capacity')
    
    if building_filter:
        rooms = rooms.filter(building_id=building_filter)
    if room_type_filter:
        rooms = rooms.filter(room_type=room_type_filter)
    if capacity_filter:
        rooms = rooms.filter(capacity__gte=capacity_filter)
    
    buildings = Building.objects.all()
    room_types = Room.ROOM_TYPE_CHOICES
    
    return render(request, 'facilities/rooms_list.html', {
        'rooms': rooms,
        'buildings': buildings,
        'room_types': room_types,
        'filters': {
            'building': building_filter,
            'room_type': room_type_filter,
            'capacity': capacity_filter,
        }
    })


@login_required
def room_detail(request, room_id):
    """Room detail with bookings and equipment"""
    room = get_object_or_404(Room.objects.select_related('building'), id=room_id)
    bookings = room.bookings.all().order_by('-starts_at')
    equipment = room.room_equipments.select_related('equipment').all()
    
    return render(request, 'facilities/room_detail.html', {
        'room': room,
        'bookings': bookings,
        'equipment': equipment
    })


@login_required
def bookings_list(request):
    """List all bookings with filters"""
    bookings = Booking.objects.select_related('room', 'created_by').all()
    
    # Apply filters
    status_filter = request.GET.get('status')
    room_filter = request.GET.get('room')
    date_filter = request.GET.get('date')
    
    if status_filter:
        if status_filter == 'pending':
            bookings = bookings.filter(is_approved=False)
        elif status_filter == 'approved':
            bookings = bookings.filter(is_approved=True)
    
    if room_filter:
        bookings = bookings.filter(room_id=room_filter)
    
    if date_filter:
        try:
            date_obj = timezone.datetime.strptime(date_filter, '%Y-%m-%d').date()
            bookings = bookings.filter(starts_at__date=date_obj)
        except ValueError:
            pass
    
    rooms = Room.objects.all()
    
    return render(request, 'facilities/bookings_list.html', {
        'bookings': bookings,
        'rooms': rooms,
        'filters': {
            'status': status_filter,
            'room': room_filter,
            'date': date_filter,
        }
    })


@login_required
def booking_create(request):
    """Create new booking"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = get_object_or_404(Room, id=data['room_id'])
            starts_at = timezone.datetime.fromisoformat(data['starts_at'])
            ends_at = timezone.datetime.fromisoformat(data['ends_at'])
            
            # Check for conflicts
            conflicts = Booking.objects.filter(
                room=room,
                starts_at__lt=ends_at,
                ends_at__gt=starts_at
            ).exists()
            
            if conflicts:
                return JsonResponse({'error': 'Booking conflicts with existing schedule'}, status=400)
            
            booking = Booking.objects.create(
                room=room,
                title=data['title'],
                purpose=data.get('purpose', ''),
                starts_at=starts_at,
                ends_at=ends_at,
                created_by=request.user
            )
            
            return JsonResponse({'success': True, 'booking_id': booking.id})
            
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    rooms = Room.objects.filter(is_active=True)
    return render(request, 'facilities/booking_create.html', {'rooms': rooms})


@login_required
def booking_approve(request, booking_id):
    """Approve a booking"""
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)
        booking.is_approved = True
        booking.save()
        messages.success(request, f'Booking "{booking.title}" has been approved.')
        return redirect('facilities:bookings_list')
    
    return redirect('facilities:bookings_list')


@login_required
def maintenance_list(request):
    """List all maintenance records"""
    maintenance_records = Maintenance.objects.select_related('room').all()
    
    status_filter = request.GET.get('status')
    if status_filter:
        maintenance_records = maintenance_records.filter(status=status_filter)
    
    return render(request, 'facilities/maintenance_list.html', {
        'maintenance_records': maintenance_records,
        'status_filter': status_filter
    })


@login_required
def equipment_list(request):
    """List all equipment"""
    equipment = Equipment.objects.all()
    return render(request, 'facilities/equipment_list.html', {'equipment': equipment})


@login_required
def analytics_dashboard(request):
    """Analytics and reporting dashboard"""
    # Room utilization statistics
    total_rooms = Room.objects.count()
    active_rooms = Room.objects.filter(is_active=True).count()
    
    # Booking statistics
    total_bookings = Booking.objects.count()
    approved_bookings = Booking.objects.filter(is_approved=True).count()
    pending_bookings = total_bookings - approved_bookings
    
    # Room type distribution
    room_type_stats = Room.objects.values('room_type').annotate(count=Count('id'))
    
    # Building capacity distribution
    building_stats = Building.objects.annotate(
        total_capacity=Count('rooms', filter=Q(rooms__is_active=True)),
        avg_capacity=Count('rooms', filter=Q(rooms__is_active=True))
    )
    
    # Recent activity
    recent_bookings = Booking.objects.select_related('room', 'created_by').order_by('-created_at')[:10]
    
    context = {
        'total_rooms': total_rooms,
        'active_rooms': active_rooms,
        'total_bookings': total_bookings,
        'approved_bookings': approved_bookings,
        'pending_bookings': pending_bookings,
        'room_type_stats': room_type_stats,
        'building_stats': building_stats,
        'recent_bookings': recent_bookings,
    }
    
    return render(request, 'facilities/analytics.html', context)


@csrf_exempt
@login_required
def api_room_availability(request, room_id):
    """Get room availability for calendar view"""
    if request.method == 'GET':
        room = get_object_or_404(Room, id=room_id)
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        
        try:
            start = timezone.datetime.fromisoformat(start_date) if start_date else timezone.now()
            end = timezone.datetime.fromisoformat(end_date) if end_date else start + timedelta(days=30)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
        
        bookings = room.bookings.filter(
            starts_at__lt=end,
            ends_at__gt=start
        ).values('id', 'title', 'starts_at', 'ends_at', 'is_approved')
        
        events = []
        for booking in bookings:
            events.append({
                'id': booking['id'],
                'title': booking['title'],
                'start': booking['starts_at'].isoformat(),
                'end': booking['ends_at'].isoformat(),
                'className': 'approved' if booking['is_approved'] else 'pending'
            })
        
        return JsonResponse(events, safe=False)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
