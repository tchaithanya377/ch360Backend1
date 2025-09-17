from rest_framework import serializers
from .models import Venue, EventCategory, Event, EventRegistration


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = '__all__'


class EventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    venue_name = serializers.ReadOnlyField(source='venue.name')

    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['created_by', 'updated_by']


class EventRegistrationSerializer(serializers.ModelSerializer):
    event_title = serializers.ReadOnlyField(source='event.title')

    class Meta:
        model = EventRegistration
        fields = '__all__'


