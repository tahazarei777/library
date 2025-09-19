# Accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from . import models
from django.db import IntegrityError

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = models.CustomUser
        fields = ('id', 'username', 'email', 'password', 'password_confirm', 
                 'first_name', 'last_name', 'phone_number', 'national_code', 'user_type')
        # user_type برای ثبت نام معمولی read-only است
        read_only_fields = ('user_type',) 

        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True},
            'phone_number': {'required': False, 'allow_blank': True},
            'national_code': {'required': False, 'allow_blank': True},
        }
    
    # اعتبارسنجی‌های تکراری unique حذف شدند.

    def validate(self, data):
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "رمز عبور با تکرار آن مطابقت ندارد."})

        data.pop('password_confirm', None)
        return data

    def create(self, validated_data):
        try:
            # استفاده از create_user برای هش کردن پسورد
            user = models.CustomUser.objects.create_user(
                username=validated_data['username'],
                email=validated_data.get('email'),
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                phone_number=validated_data.get('phone_number', ''),
                national_code=validated_data.get('national_code', ''),
                # user_type پیش فرض از مدل گرفته می‌شود
            )
            return user
        except IntegrityError as e:
            # هندل کردن ارورهای یونیک بودن فیلدها
            error_message = str(e)
            if 'email' in error_message:
                raise serializers.ValidationError({'email': ['این ایمیل قبلاً ثبت شده است']})
            elif 'username' in error_message:
                raise serializers.ValidationError({'username': ['این نام کاربری قبلاً ثبت شده است']})
            elif 'national_code' in error_message:
                raise serializers.ValidationError({'national_code': ['این کد ملی قبلاً ثبت شده است']})
            elif 'phone_number' in error_message:
                raise serializers.ValidationError({'phone_number': ['این شماره تلفن قبلاً ثبت شده است']})
            raise serializers.ValidationError('خطا در ایجاد کاربر')

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('حساب کاربری غیرفعال است.')
            else:
                raise serializers.ValidationError('نام کاربری یا رمز عبور اشتباه است.')
        else:
            raise serializers.ValidationError('لطفاً نام کاربری و رمز عبور را وارد کنید.')
        
        return data