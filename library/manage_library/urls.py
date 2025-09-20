"""
URL configuration for manage_library project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include,re_path
import rest_framework
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="DIR_API",
        default_version = 'v1',
        descriptions = "URL LINKS OF MY API ",
        terms_of_service="http://127.0.0.1:8000",
        contact = openapi.Contact(email="momad6955@gmail.com"),
        license = openapi.License(name="BSD License")
    ),
    public=True,
    permission_classes = (permissions.AllowAny,),
)




urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('Accounts.urls')),
    path('api/library/', include('Book.urls')),
    # path("api/country/", include('country.urls')),
    path("api/", include('rest_framework.urls')),
    path("swagger<format>/", schema_view.without_ui(cache_timeout=0),name="schema-json"),
    path("swagger/", schema_view.with_ui('swagger',cache_timeout=0), name="schema-swagger-ui"),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc')

]
