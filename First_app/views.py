from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import models
from .models import Category, Book, Transaction, Inventory
from .serializers import (CategorySerializer, BookSerializer, TransactionSerializer, 
                         BookRequestSerializer, ReturnBooksSerializer, InventorySerializer)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        category = self.get_object()
        books = category.books.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author']
    search_fields = ['title', 'author', 'description', 'isbn']
    ordering_fields = ['title', 'author', 'price', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def available_books(self, request):
        books = Book.objects.filter(available_count__gt=0)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category_id = request.query_params.get('category_id')
        if category_id:
            books = Book.objects.filter(category_id=category_id)
        else:
            books = Book.objects.all()
        
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        books = Book.objects.filter(
            models.Q(title__icontains=query) | 
            models.Q(author__icontains=query) |
            models.Q(category__name__icontains=query)
        )
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'book__category']
    ordering_fields = ['created_at', 'total_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def request_book(self, request):
        serializer = BookRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            book_id = serializer.validated_data['book_id']
            transaction_type = serializer.validated_data['transaction_type']
            quantity = serializer.validated_data['quantity']
            
            try:
                book = Book.objects.get(id=book_id)
                
                if book.available_count < quantity:
                    return Response(
                        {'error': 'تعداد کتاب درخواستی بیش از حد موجود است!'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
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
    
    @action(detail=True, methods=['post'])
    def return_books(self, request, pk=None):
        transaction = self.get_object()
        return_quantity = request.data.get('quantity', transaction.quantity)
        
        try:
            transaction.return_books(return_quantity)
            serializer = self.get_serializer(transaction)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def active_loans(self, request):
        active_loans = self.get_queryset().filter(
            transaction_type=Book.LOAN,
            is_completed=False
        )
        serializer = self.get_serializer(active_loans, many=True)
        return Response(serializer.data)

class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def replenish(self, request, pk=None):
        inventory = self.get_object()
        inventory.check_and_replenish()
        serializer = self.get_serializer(inventory)
        return Response(serializer.data)