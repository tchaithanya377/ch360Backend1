from rest_framework import serializers
from .models import Building, Room, Equipment, RoomEquipment, Booking, Maintenance


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'


class RoomEquipmentSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(), source='equipment', write_only=True
    )

    class Meta:
        model = RoomEquipment
        fields = ['id', 'room', 'equipment', 'equipment_id', 'quantity']


class RoomSerializer(serializers.ModelSerializer):
    room_equipments = RoomEquipmentSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

    def validate(self, attrs):
        instance = Booking(**attrs)
        instance.clean()
        return attrs


class MaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maintenance
        fields = '__all__'


