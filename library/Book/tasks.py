# Book/tasks.py
from django.utils import timezone
from celery import shared_task
from .models import Transaction, Book
from django.db import transaction

# این وظیفه باید در settings.py تنظیم شود تا Celery Beat آن را اجرا کند.
@shared_task
def auto_return_loaned_books_task():
    """
    وظیفه زمانبندی شده برای بررسی تراکنش‌های قرضی ناتمام و منقضی شده (1 روز).
    """
    
    # پیدا کردن تراکنش‌های قرضی (LOAN) که تکمیل نشده‌اند و مهلت آن‌ها گذشته است.
    # deadline_date__lte=timezone.now()
    overdue_transactions = Transaction.objects.filter(
        transaction_type=Book.LOAN,
        is_completed=False,
        deadline_date__lte=timezone.now() 
    ).select_related('book') # بهینه‌سازی: لود همزمان book
    
    returned_count = 0
    
    for trans in overdue_transactions:
        # فراخوانی متد اتمیک return_books از مدل
        if trans.return_books(): 
            returned_count += 1
            
    # این خروجی فقط برای لاگ Celery Worker است
    print(f"وظیفه بازگشت خودکار کتاب‌ها تکمیل شد. تعداد بازگشتی: {returned_count}")
    return returned_count