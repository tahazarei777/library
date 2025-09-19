from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Book, Transaction, Inventory

@receiver(post_save, sender=Book)
def create_inventory_for_book(sender, instance, created, **kwargs):
    if created:
        Inventory.objects.create(book=instance)

@receiver(post_save, sender=Transaction)
def auto_replenish_after_transaction(sender, instance, created, **kwargs):
    if created and instance.transaction_type == Book.PURCHASE:
        try:
            inventory = Inventory.objects.get(book=instance.book)
            inventory.check_and_replenish()
        except Inventory.DoesNotExist:
            pass