from rest_framework import serializers
from .models import Category, Book, Transaction, Inventory

class CategorySerializer(serializers.ModelSerializer):
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'books_count', 'created_at']
    
    def get_books_count(self, obj):
        return obj.books.count()

class BookSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'description', 'category', 'category_name',
            'total_count', 'available_count', 'price', 'isbn', 'published_date',
            'created_at', 'updated_at'
        ]


class TransactionSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)
    book_category = serializers.CharField(source='book.category.name', read_only=True)
    deadline_date = serializers.DateTimeField(read_only=True) # ADDED
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'book', 'book_title', 'book_author', 'book_category',
            'transaction_type', 'quantity', 'total_price', 'created_at', 'deadline_date', 'is_completed'
        ]
        read_only_fields = ['user', 'total_price', 'is_completed', 'deadline_date']


class BookRequestSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=Book.TRANSACTION_TYPES)
    quantity = serializers.IntegerField(min_value=1, default=1)


class InventorySerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    
    class Meta:
        model = Inventory
        fields = '__all__'

class BookStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'total_count', 'available_count']
        read_only_fields = ['id', 'title', 'author']

class BookStockUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['total_count', 'available_count']

    def validate(self, data):
        available = data.get('available_count', self.instance.available_count)
        total = data.get('total_count', self.instance.total_count)
        if available > total:
            raise serializers.ValidationError("تعداد موجود نمی‌تواند از تعداد کل بیشتر باشد")
        return data



