from rest_framework import viewsets, status, permissions, filters,mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import models
from .models import Category, Book, Transaction, Inventory
from .permissions import IsAdminOrLibrarian, IsAdminOrStorekeeper,IsStorekeeper,IsAdmin
from rest_framework.views import APIView
from django.db import models, transaction
from .serializers import (CategorySerializer, BookSerializer, TransactionSerializer, 
                         BookRequestSerializer, InventorySerializer,
                         BookStoreSerializer, BookStockUpdateSerializer)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrLibrarian] 
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrLibrarian])
    def books(self, request, pk=None):
        category = self.get_object()
        books = category.books.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author']
    search_fields = ['title', 'author', 'description', 'isbn']
    ordering_fields = ['price']
    ordering = ['-price']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'available_books', 'by_category', 'search']:
            return [IsAdmin()] 
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrLibrarian()] 
        elif self.action in ['store_view', 'update_stock']:
            return [IsStorekeeper()]  
        else:
            return [IsAdminOrLibrarian()] 
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.request.user.user_type == 'storekeeper':
            return queryset.only('id', 'title', 'author', 'total_count', 'available_count')
        
        return queryset
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def available_books(self, request):
        books = Book.objects.filter(available_count__gt=0)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def by_category(self, request):
        category_id = request.query_params.get('category_id')
        if category_id:
            books = Book.objects.filter(category_id=category_id)
        else:
            books = Book.objects.all()
        
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def search(self, request):
        query = request.query_params.get('q', '')
        books = Book.objects.filter(
            models.Q(title__icontains=query) | 
            models.Q(author__icontains=query) |
            models.Q(category__name__icontains=query)
        )
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrLibrarian])
    def return_books(self, request, pk=None):
        transaction = self.get_object()
        return_quantity = request.data.get('quantity', transaction.quantity)
        
        try:
            transaction.return_books(return_quantity)
            serializer = self.get_serializer(transaction)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminOrStorekeeper])
    def store_manage(self, request, pk=None):
        if request.method == 'GET':
            books = Book.objects.all().only(
                'id', 'title', 'author', 'total_count', 'available_count'
            )
            serializer = BookStoreSerializer(books, many=True)
            return Response(serializer.data)
    
        elif request.method == 'PATCH':
            book_id = request.data.get('book_id')
            if not book_id:
                return Response({'error': 'شناسه کتاب ارسال نشده'}, status=status.HTTP_400_BAD_REQUEST)
    
            try:
                book = Book.objects.get(id=book_id)
            except Book.DoesNotExist:
                return Response({'error': 'کتاب یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
    
            allowed_fields = ['total_count', 'available_count']
            data = {key: request.data.get(key) for key in allowed_fields if key in request.data}
    
            if not data:
                return Response({'error': 'هیچ فیلد مجازی برای آپدیت ارسال نشده'}, status=status.HTTP_400_BAD_REQUEST)
    
            if 'available_count' in data and data['available_count'] > book.total_count:
                return Response({'error': 'تعداد موجود نمی‌تواند از تعداد کل بیشتر باشد'}, status=status.HTTP_400_BAD_REQUEST)
    
            serializer = BookStockUpdateSerializer(book, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [IsAdminOrStorekeeper]  
    
    def get_queryset(self):
        if self.request.user.user_type == 'storekeeper':
            return Inventory.objects.filter(book__available_count__gt=0)
        elif self.request.user.user_type == 'admin':
            return Inventory.objects.all()
        else:
            return Inventory.objects.none()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrStorekeeper])
    def replenish(self, request, pk=None):
        inventory = self.get_object()
        inventory.check_and_replenish()
        serializer = self.get_serializer(inventory)
        return Response(serializer.data)

class StorekeeperDashboardView(APIView):
    permission_classes = [IsStorekeeper]

    def get(self, request):
        books = Book.objects.only('id', 'title', 'author', 'total_count', 'available_count')
        low_stock_books = books.filter(available_count__lt=5)
        out_of_stock_books = books.filter(available_count=0)
        serializer = BookStoreSerializer(books, many=True)
        return Response({
            'books': serializer.data,
            'stats': {
                'total_books': books.count(),
                'low_stock_books': low_stock_books.count(),
                'out_of_stock_books': out_of_stock_books.count(),
            }
        })

    def patch(self, request):
        updates = request.data.get('updates', [])
        results = []
        for update in updates:
            book_id = update.get('book_id')
            try:
                book = Book.objects.get(id=book_id)
                serializer = BookStockUpdateSerializer(book, data=update, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    results.append({'book_id': book_id, 'status': 'success', 'message': 'موجودی با موفقیت به‌روز شد'})
                else:
                    results.append({'book_id': book_id, 'status': 'error', 'message': serializer.errors})
            except Book.DoesNotExist:
                results.append({'book_id': book_id, 'status': 'error', 'message': 'کتاب یافت نشد'})
        return Response({'results': results}, status=status.HTTP_200_OK)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):

    """مشاهده تاریخچه تراکنش‌ها (فقط خواندنی)"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        # کاربران فقط تراکنش‌های خود را می‌بینند
        if self.request.user.user_type == 'admin':
            return Transaction.objects.all()
        return Transaction.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated]) 
    @transaction.atomic # تضمین اجرای کامل یا عدم اجرای هیچکدام
    def request_book(self, request):
        serializer = BookRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            book_id = serializer.validated_data['book_id']
            transaction_type = serializer.validated_data['transaction_type']
            quantity = serializer.validated_data['quantity']
            
            try:
                book = Book.objects.select_for_update().get(id=book_id) 
                
                if book.available_count < quantity:
                    return Response(
                        {'error': 'تعداد کتاب درخواستی بیش از حد موجود است!'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 1. کسر موجودی از انبار
                book.available_count -= quantity
                book.save(update_fields=['available_count']) 
                
                # 2. ایجاد تراکنش (save() مهلت و قیمت را تنظیم می‌کند)
                transaction = Transaction.objects.create(
                    user=request.user,
                    book=book,
                    transaction_type=transaction_type,
                    quantity=quantity
                )
                
                result_serializer = TransactionSerializer(transaction)
                return Response(result_serializer.data, status=status.HTTP_201_CREATED)
                
            except Book.DoesNotExist:
                return Response(
                    {'error': 'کتاب مورد نظر یافت نشد!'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookStockUpdateViewSet(mixins.UpdateModelMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    queryset = Book.objects.only('id', 'title', 'author', 'total_count', 'available_count')
    serializer_class = BookStockUpdateSerializer
    permission_classes = [IsStorekeeper]

