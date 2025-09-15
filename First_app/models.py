from django.db import models
from Account.models import CustomeUser as  User
from django.utils import timezone

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
    
    class Meta:
        verbose_name = "کتاب"
        verbose_name_plural = "کتاب‌ها"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.author}"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="کتاب")
    transaction_type = models.CharField(
        max_length=10, 
        choices=Book.TRANSACTION_TYPES, 
        verbose_name="نوع تراکنش"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="قیمت کل")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")
    
    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if self.is_completed:
            super().save(*args, **kwargs)
            return
            
        if self.book.available_count < self.quantity:
            raise ValueError("تعداد کتاب درخواستی بیش از حد موجود است!")
        
        if self.transaction_type == Book.PURCHASE:
            self.total_price = self.book.price * self.quantity
        
        self.book.available_count -= self.quantity
        self.book.save()
        
        super().save(*args, **kwargs)
        self.replenish_stock()
    
    def replenish_stock(self):
        if self.transaction_type == Book.PURCHASE:
            if self.book.total_count >= self.quantity:
                self.book.total_count -= self.quantity
                self.book.save()
            else:
                raise ValueError("تعداد کتاب درخواستی بیش از حد موجود در انبار است!")
        
        self.is_completed = True
        self.save()
    
    def return_books(self, return_quantity=None):
        if self.transaction_type != Book.LOAN:
            raise ValueError("فقط کتاب‌های قرضی قابل بازگرداندن هستند!")
        
        if return_quantity is None:
            return_quantity = self.quantity
        
        if return_quantity > self.quantity:
            raise ValueError("تعداد بازگردانی بیش از حد مجاز است!")
        
        self.book.available_count += return_quantity
        self.book.save()
        
        self.quantity -= return_quantity
        if self.quantity == 0:
            self.is_completed = True
        
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.get_transaction_type_display()}"

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