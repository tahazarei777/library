from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from geonamescache import GeonamesCache
from .models import UserLocation
from .serializers import (
    CountrySerializer, 
    ProvinceSerializer, 
    CitySerializer, 
    UserLocationSerializer
)

class GeoDataManager:
    def __init__(self):
        self.gc = GeonamesCache()
        self.countries_data = self.gc.get_countries()
        self.cities_data = self.gc.get_cities()
    
    def get_countries(self):
        """دریافت لیست همه کشورها"""
        countries = []
        for code, data in self.countries_data.items():
            countries.append({
                'name': data['name'],
                'code': code
            })
        return sorted(countries, key=lambda x: x['name'])
    
    def get_provinces(self, country_code):
        """دریافت استان‌های یک کشور"""
        provinces = set()
        for city_data in self.cities_data.values():
            if (city_data['countrycode'] == country_code and 
                city_data.get('admin1name') and 
                city_data['admin1name'] != 'Unknown'):
                provinces.add(city_data['admin1name'])
        return sorted(list(provinces))
    
    def get_cities(self, country_code, province_name):
        """دریافت شهرهای یک استان"""
        cities = []
        for city_data in self.cities_data.values():
            if (city_data['countrycode'] == country_code and 
                city_data.get('admin1name') and 
                city_data['admin1name'] == province_name):
                cities.append(city_data['name'])
        return sorted(cities)

geo_manager = GeoDataManager()

@api_view(['GET'])
@permission_classes([AllowAny])
def countries_list(request):
    """لیست همه کشورها"""
    countries = geo_manager.get_countries()
    serializer = CountrySerializer(countries, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def provinces_list(request, country_code):
    """لیست استان‌های یک کشور"""
    provinces = geo_manager.get_provinces(country_code.upper())
    serializer = ProvinceSerializer([{'name': p} for p in provinces], many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def cities_list(request, country_code, province_name):
    """لیست شهرهای یک استان"""
    cities = geo_manager.get_cities(country_code.upper(), province_name)
    serializer = CitySerializer([{'name': c} for c in cities], many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def save_location(request):
    """ذخیره موقعیت کاربر"""
    serializer = UserLocationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLocationListView(generics.ListAPIView):
    """لیست موقعیت‌های ذخیره شده"""
    queryset = UserLocation.objects.all().order_by('-created_at')
    serializer_class = UserLocationSerializer