# pyrefly: ignore [missing-import]
from rest_framework import serializers
from .models import Transaction
from tours.serializers import CustomTourSerializer

class TransactionSerializer(serializers.ModelSerializer):
    custom_tour_detail = CustomTourSerializer(source='custom_tour', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ('id', 'custom_tour', 'custom_tour_detail', 'transaction_id', 'amount', 'payment_method', 'status', 'created_at')
        read_only_fields = ('id', 'transaction_id', 'amount', 'status', 'created_at')
