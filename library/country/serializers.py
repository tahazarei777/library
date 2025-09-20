from rest_framework import serializers
from .models import UserLocation

class CountrySerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()

class ProvinceSerializer(serializers.Serializer):
    name = serializers.CharField()

class CitySerializer(serializers.Serializer):
    name = serializers.CharField()

class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = ['id', 'country', 'province', 'city', 'created_at']
        read_only_fields = ['created_at']