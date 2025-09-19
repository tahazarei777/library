from django.contrib import admin
from .models import Category, Book, Transaction, Inventory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'books_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    
    def books_count(self, obj):
        return obj.books.count()
    books_count.short_description = 'تعداد کتاب‌ها'

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'available_count', 'total_count', 'price']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'author', 'isbn']
    list_editable = ['available_count', 'total_count', 'price']
    raw_id_fields = ['category']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'transaction_type', 'quantity', 'total_price', 'created_at', 'is_completed']
    list_filter = ['transaction_type', 'created_at', 'is_completed']
    search_fields = ['user__username', 'book__title']
    readonly_fields = ['created_at']

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['book', 'min_stock_level', 'max_stock_level', 'auto_replenish', 'last_replenished']
    list_filter = ['auto_replenish']
    search_fields = ['book__title']