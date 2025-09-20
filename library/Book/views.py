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
from .serializers import (CategorySerializer, BookSerializer, TransactionSerializer,BookRequestSerializer, InventorySerializer,BookStoreSerializer, BookStockUpdateSerializer)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrLibrarian]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrLibrarian])
    def books(self, request, pk=None):
        category = self.get_object()
        books = Book.objects.filter(category=category) 
        page = self.paginate_queryset(books)
        if page is not None:
            serializer = BookSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
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
        if self.action in ['list', 'retrieve']:
            return [IsAdmin()] 
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrLibrarian()] 
        elif self.action in ['store_manage', 'store_view']:
            return [IsStorekeeper()]  
        else:
            return [IsAdminOrLibrarian()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.request.user.user_type == 'storekeeper':
            return queryset.only('id', 'title', 'author', 'total_count', 'available_count')
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'store_view':
            return BookStoreSerializer
        elif self.action == 'store_manage':
            return BookStockUpdateSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['get'])
    def available_books(self, request):
        books = Book.objects.filter(available_count__gt=0)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def store_view(self, request):
        books = self.get_queryset()
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def store_manage(self, request, pk=None):
        book = self.get_object()
        
        allowed_fields = ['total_count', 'available_count']
        data = {key: request.data.get(key) for key in allowed_fields if key in request.data}
        
        if not data:
            return Response({'error': 'هیچ فیلد مجازی برای آپدیت ارسال نشده'}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'available_count' in data and data['available_count'] > book.total_count:
            return Response({'error': 'تعداد موجود نمی‌تواند از تعداد کل بیشتر باشد'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(book, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [IsAdminOrStorekeeper]
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'user_type'):
            if user.user_type == 'storekeeper':
                return Inventory.objects.filter(book__available_count__gt=0)
            elif user.user_type == 'admin':
                return Inventory.objects.all()
        
        return Inventory.objects.none()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrStorekeeper])
    def replenish(self, request, pk=None):
        inventory = self.get_object()
        if hasattr(inventory, 'check_and_replenish'):
            try:
                inventory.check_and_replenish()
                inventory.refresh_from_db()
                serializer = self.get_serializer(inventory)
                return Response(serializer.data)
            except Exception as e:
                return Response(
                    {'error': f'خطا در replenish: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'متد check_and_replenish وجود ندارد'},
                status=status.HTTP_400_BAD_REQUEST
            )

class StorekeeperDashboardView(APIView):
    permission_classes = [IsStorekeeper]

    def get(self, request):
        # فقط یک query به دیتابیس با annotate برای کارایی بهتر
        books_data = Book.objects.aggregate(
            total_books=models.Count('id'),
            low_stock_books=models.Count('id', filter=models.Q(available_count__lt=5)),
            out_of_stock_books=models.Count('id', filter=models.Q(available_count=0))
        )
        
        # گرفتن کتاب‌ها با pagination
        books = Book.objects.only('id', 'title', 'author', 'total_count', 'available_count')
        page = self.paginate_queryset(books)
        if page is not None:
            serializer = BookStoreSerializer(page, many=True)
            return self.get_paginated_response({
                'books': serializer.data,
                'stats': books_data
            })
        
        serializer = BookStoreSerializer(books, many=True)
        return Response({
            'books': serializer.data,
            'stats': books_data
        })
    
    def paginate_queryset(self, queryset):
        # پیاده‌سازی ساده pagination
        page_size = self.request.query_params.get('page_size', 20)
        page = self.request.query_params.get('page', 1)
        
        try:
            page_size = int(page_size)
            page = int(page)
        except (ValueError, TypeError):
            return None
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return list(queryset[start:end])

    def patch(self, request):
        updates = request.data.get('updates', [])
        
        # بررسی محدودیت تعداد به روزرسانی‌ها در یک درخواست
        if len(updates) > 50:
            return Response(
                {'error': 'تعداد به روزرسانی‌ها نمی‌تواند بیشتر از ۵۰ مورد باشد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        successful_updates = 0
        
        for update in updates:
            book_id = update.get('book_id')
            if not book_id:
                results.append({
                    'book_id': None, 
                    'status': 'error', 
                    'message': 'شناسه کتاب ارائه نشده'
                })
                continue
                
            try:
                book = Book.objects.get(id=book_id)
                
                # بررسی اینکه کاربر به این کتاب دسترسی دارد
                # (اگر نیاز به کنترل دسترسی دقیق‌تر دارید)
                
                serializer = BookStockUpdateSerializer(
                    book, 
                    data=update, 
                    partial=True,
                    context={'request': request}  # افزودن context برای دسترسی به request در serializer
                )
                
                if serializer.is_valid():
                    serializer.save()
                    results.append({
                        'book_id': book_id, 
                        'status': 'success', 
                        'message': 'موجودی با موفقیت به‌روز شد'
                    })
                    successful_updates += 1
                else:
                    results.append({
                        'book_id': book_id, 
                        'status': 'error', 
                        'message': serializer.errors
                    })
            except Book.DoesNotExist:
                results.append({
                    'book_id': book_id, 
                    'status': 'error', 
                    'message': 'کتاب یافت نشد'
                })
            except Exception as e:
                results.append({
                    'book_id': book_id, 
                    'status': 'error', 
                    'message': f'خطای سیستمی: {str(e)}'
                })
        
        return Response({
            'results': results,
            'summary': {
                'total_updates': len(updates),
                'successful_updates': successful_updates,
                'failed_updates': len(updates) - successful_updates
            }
        }, status=status.HTTP_200_OK)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        if self.request.user.user_type == 'admin':
            return Transaction.objects.all()
        return Transaction.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated]) 
    @transaction.atomic
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
                
                book.available_count -= quantity
                book.save(update_fields=['available_count']) 
                
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

