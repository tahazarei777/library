from django.db import models
from Accounts.models import CustomUser
from django.utils import timezone
from django.db import models, transaction
from Accounts.models import CustomUser
from django.utils import timezone
from datetime import timedelta 

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
class Book(models.Model):
    LOAN = 'loan'
    PURCHASE = 'purchase'
    TRANSACTION_TYPES = [
        (LOAN, 'قرض'),
        (PURCHASE, 'خرید'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="عنوان کتاب")
    author = models.CharField(max_length=100, verbose_name="نویسنده")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='books',
        verbose_name="دسته‌بندی"
    )
    total_count = models.PositiveIntegerField(default=100, verbose_name="تعداد کل در انبار")
    available_count = models.PositiveIntegerField(default=10, verbose_name="تعداد موجود")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="قیمت")
    isbn = models.CharField(max_length=13, blank=True, verbose_name="شابک")
    published_date = models.DateField(null=True, blank=True, verbose_name="تاریخ انتشار")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    @classmethod
    def get_store_visible_books(cls):
        return cls.objects.all().only(
            'id', 'title', 'author', 'total_count', 'available_count'
        )
    class Meta:
        verbose_name = "کتاب"
        verbose_name_plural = "کتاب‌ها"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.author}"

class Transaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions', verbose_name="کاربر")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='transactions', verbose_name="کتاب")
    transaction_type = models.CharField(max_length=10, choices=Book.TRANSACTION_TYPES, verbose_name="نوع تراکنش")
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="قیمت نهایی")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    
    deadline_date = models.DateTimeField(null=True, blank=True, verbose_name="مهلت بازگشت") 

    class Meta:
        # ... (کدهای قبلی) ...
        pass

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.get_transaction_type_display()})"

    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if is_new:
            self.total_price = self.book.price * self.quantity
            
            # 1. Set deadline for LOAN
            if self.transaction_type == Book.LOAN:
                self.deadline_date = timezone.now() + timedelta(days=1) 
        
        super().save(*args, **kwargs)

    @transaction.atomic # اجرای اتمیک برای حفظ یکپارچگی داده‌ها
    def return_books(self, quantity=None):
        """بازگرداندن کتاب به انبار و تکمیل تراکنش قرضی به صورت اتمیک."""
        
        if self.transaction_type != Book.LOAN or self.is_completed:
            return False 

        # در بازگشت خودکار، تمام کتاب‌های این تراکنش را برمی‌گردانیم
        quantity_to_return = self.quantity 
        
        book = self.book
        
        # 1. افزایش موجودی در دسترس
        book.available_count += quantity_to_return
        
        # 2. تکمیل تراکنش
        self.is_completed = True
        
        book.save(update_fields=['available_count'])
        self.save(update_fields=['is_completed'])
        
        return True

class Inventory(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='inventory')
    min_stock_level = models.PositiveIntegerField(default=5, verbose_name="حداقل موجودی")
    max_stock_level = models.PositiveIntegerField(default=50, verbose_name="حداکثر موجودی")
    auto_replenish = models.BooleanField(default=True, verbose_name="پر کردن خودکار موجودی")
    last_replenished = models.DateTimeField(auto_now=True, verbose_name="آخرین پر کردن موجودی")
    
    class Meta:
        verbose_name = "مدیریت انبار"
        verbose_name_plural = "مدیریت انبار"
    
    def check_and_replenish(self):
        if not self.auto_replenish:
            return
            
        if self.book.available_count < self.min_stock_level:
            needed = self.max_stock_level - self.book.available_count
            
            if self.book.total_count >= needed:
                self.book.available_count += needed
                self.book.total_count -= needed
                self.book.save()
                self.last_replenished = timezone.now()
                self.save()
            elif self.book.total_count > 0:
                self.book.available_count += self.book.total_count
                self.book.total_count = 0
                self.book.save()
                self.last_replenished = timezone.now()
                self.save()
    
    def __str__(self):
        return f"انبار {self.book.title}"