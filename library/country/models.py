from django.db import models

class UserLocation(models.Model):
    country = models.CharField(max_length=100)
    country_code = models.CharField(max_length=2)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "موقعیت کاربر"
        verbose_name_plural = "موقعیت‌های کاربران"
    
    def __str__(self):
        return f"{self.country} - {self.province} - {self.city}"