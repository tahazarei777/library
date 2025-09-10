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
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        source='category', 
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'description', 'category', 'category_name', 'category_id',
            'total_count', 'available_count', 'price', 'isbn', 'published_date',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'category': {'read_only': True}
        }

class TransactionSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)
    book_category = serializers.CharField(source='book.category.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'book', 'book_title', 'book_author', 'book_category',
            'transaction_type', 'quantity', 'total_price', 'created_at', 'is_completed'
        ]
        read_only_fields = ['user', 'total_price', 'is_completed']

class BookRequestSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=Book.TRANSACTION_TYPES)
    quantity = serializers.IntegerField(min_value=1, default=1)

class ReturnBooksSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, required=False)

class InventorySerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    
    class Meta:
        model = Inventory
        fields = '__all__'