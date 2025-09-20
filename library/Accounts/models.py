# Accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import validate_slug, RegexValidator

class CustomUser(AbstractUser):
    # Validators
    phone_regex = RegexValidator(
        regex=r'^(\+98|0)?9\d{9}$', # اصلاح Regex برای فرمت‌های رایج ایران
        message="شماره تلفن باید در فرمت صحیح وارد شود (مثال: 0912xxxxxxx)"
    )
    national_code_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="کد ملی باید 10 رقم باشد"
    )
    
    # User Types
    class UserType(models.TextChoices):
        ADMIN = 'admin', 'مدیر'
        LIBRARIAN = 'librarian', 'کتابدار'
        STOREKEEPER = 'storekeeper', 'انباردار'
    
    # Fields
    username = models.CharField(
        max_length=150,
        verbose_name='نام کاربری',
        unique=True,
        validators=[validate_slug],
        error_messages={
            'unique': "این نام کاربری قبلاً ثبت شده است",
        }
    )
    
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.STOREKEEPER, # پیش‌فرض کتابدار یا باید یک "عضو" معمولی باشد
        verbose_name="نقش کاربر"
    )
    
    phone_number = models.CharField(
        max_length=15,
        validators=[phone_regex],
        unique=False, # فرض می‌کنیم شماره تلفن یونیک است
        blank=True,
        null=True,
        verbose_name="شماره تلفن"
    )
    
    national_code = models.CharField(
        max_length=10,
        validators=[national_code_regex],
        unique=True, # فرض می‌کنیم کد ملی یونیک است
        blank=True,
        null=True,
        verbose_name="کد ملی"
    )

    # EMAIL_FIELD = 'email'
    
    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        
    def __str__(self):
        return self.username