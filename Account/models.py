from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomeUser(AbstractUser):
    national_code = models.CharField(max_length=50,verbose_name='کد ملی:')