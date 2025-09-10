from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, BookViewSet, TransactionViewSet, InventoryViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet,basename='category')
router.register(r'books', BookViewSet,basename='books')
router.register(r'transactions', TransactionViewSet,basename='transactions')
router.register(r'inventory', InventoryViewSet,basename='invertory')

urlpatterns = [
    path('', include(router.urls)),
]