from django.contrib import admin
from . import models


@admin.register(models.CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'phone_number', 'is_staff', 'is_active']
# Register your models here.
