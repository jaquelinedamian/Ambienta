from rest_framework import serializers
from .models import Reading, FanState

class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reading
        fields = ['id', 'temperature', 'timestamp']
        read_only_fields = ['timestamp']
        extra_kwargs = {'temperature': {'required': False}}

class FanStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FanState
        fields = '__all__'