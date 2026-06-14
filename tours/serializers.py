from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.serializers import UserSerializer
from .models import Destination, TourPackage, CustomTour, ItineraryItem, ApprovalLog

User = get_user_model()

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = '__all__'

class ItineraryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItineraryItem
        fields = ('id', 'day_number', 'activity_title', 'activity_description', 'estimated_cost')

class TourPackageSerializer(serializers.ModelSerializer):
    itinerary_items = ItineraryItemSerializer(many=True, read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)

    class Meta:
        model = TourPackage
        fields = (
            'id', 'title', 'description', 'duration_days', 'price',
            'is_active', 'created_by', 'created_by_detail', 'itinerary_items', 'created_at'
        )

class CustomTourSerializer(serializers.ModelSerializer):
    itinerary_items = ItineraryItemSerializer(many=True, required=False)
    client = UserSerializer(read_only=True)
    assigned_manager_detail = UserSerializer(source='assigned_manager', read_only=True)
    assigned_approver_detail = UserSerializer(source='assigned_approver', read_only=True)

    class Meta:
        model = CustomTour
        fields = (
            'id', 'client', 'title', 'start_date', 'end_date', 'status',
            'assigned_manager', 'assigned_manager_detail',
            'assigned_approver', 'assigned_approver_detail',
            'base_cost', 'service_fee', 'markup_amount', 'total_price',
            'ai_analysis', 'itinerary_items', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'client', 'status', 'base_cost', 'service_fee', 'total_price', 'ai_analysis'
        )

    def create(self, validated_data):
        itinerary_data = validated_data.pop('itinerary_items', [])
        validated_data['client'] = self.context['request'].user
        
        custom_tour = CustomTour.objects.create(**validated_data)
        
        for item in itinerary_data:
            ItineraryItem.objects.create(custom_tour=custom_tour, **item)
            
        custom_tour.recalculate_prices()
        custom_tour.save()
        return custom_tour

    def update(self, instance, validated_data):
        itinerary_data = validated_data.pop('itinerary_items', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if itinerary_data is not None:
            instance.itinerary_items.all().delete()
            for item in itinerary_data:
                ItineraryItem.objects.create(custom_tour=instance, **item)
        
        instance.recalculate_prices()
        instance.save()
        return instance

class ApprovalLogSerializer(serializers.ModelSerializer):
    acted_by_detail = UserSerializer(source='acted_by', read_only=True)

    class Meta:
        model = ApprovalLog
        fields = ('id', 'custom_tour', 'acted_by', 'acted_by_detail', 'from_status', 'to_status', 'comments', 'created_at')
