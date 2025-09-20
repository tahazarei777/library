from django.urls import path
from . import views

urlpatterns = [
    path('countries/', views.countries_list, name='countries-list'),
    path('countries/<str:country_code>/provinces/', views.provinces_list, name='provinces-list'),
    path('countries/<str:country_code>/provinces/<str:province_name>/cities/', 
         views.cities_list, name='cities-list'),
    path('save-location/', views.save_location, name='save-location'),
    path('saved-locations/', views.UserLocationListView.as_view(), name='saved-locations'),
]