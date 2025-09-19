# Accounts/views.py
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from . import models
from .serializers import UserSerializer, LoginSerializer
from Book.permissions import IsAdmin # برای دسترسی ادمین به UserViewSet

class UserViewSet(viewsets.ModelViewSet):
    """مدیریت کاربران توسط ادمین"""
    queryset = models.CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin] 
    
    # perform_create حذف شد (توسط serializer.create مدیریت می‌شود)

class RegisterView(generics.CreateAPIView):
    """ثبت نام کاربر جدید"""
    queryset = models.CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """ورود کاربر و دریافت JWT و Session"""
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user) # ایجاد Session
        refresh = RefreshToken.for_user(user) # ایجاد JWT
        return Response({
            'user': UserSerializer(user).data, # از سریالایزر استفاده می‌کند
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """خروج کاربر (حذف Session)"""
    logout(request)
    # برای خروج کامل از JWT، کاربر باید refresh token را Blacklist کند
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        pass # اگر refresh token ارسال نشد، مشکلی نیست
        
    return Response({'message': 'با موفقیت خارج شدید.'}, status=status.HTTP_205_RESET_CONTENT)

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """مشاهده و ویرایش پروفایل کاربر"""
    user = request.user
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
        
    elif request.method in ['PUT', 'PATCH']:
        # حذف فیلدهای حساس و فقط خواندنی
        data = request.data.copy()
        data.pop('password', None)
        data.pop('password_confirm', None)
        
        serializer = UserSerializer(user, data=data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)