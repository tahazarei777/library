from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, BookViewSet, TransactionViewSet, InventoryViewSet,StorekeeperDashboardView
from .views import BookStockUpdateViewSet
router = DefaultRouter()
router.register(r'categories', CategoryViewSet,basename='category')
router.register(r'books', BookViewSet,basename='books')
router.register(r'transactions', TransactionViewSet,basename='transactions')
router.register(r'inventory', InventoryViewSet,basename='invertory')
router.register(r'storekeeper/books', BookStockUpdateViewSet, basename='storekeeper-books')




urlpatterns = [
    path('', include(router.urls)),
    path('storekeeper/dashboard/', StorekeeperDashboardView.as_view(), name='storekeeper-dashboard'),
]