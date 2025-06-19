from django.db import models
from django.conf import settings
from pharmacies.models import Pharmacy
from inventory.models import Inventory


class Sale(models.Model):
    """Model for sales transactions"""
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('INSURANCE', 'Insurance'),
        ('CREDIT', 'Credit'),
    ]
    
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='sales')
    sale_number = models.CharField(max_length=100, unique=True)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Sale {self.sale_number} - {self.pharmacy.name}"
    
    def save(self, *args, **kwargs):
        if not self.sale_number:
            # Generate sale number
            from django.utils import timezone
            today = timezone.now().date()
            count = Sale.objects.filter(created_at__date=today).count() + 1
            self.sale_number = f"SALE-{today.strftime('%Y%m%d')}-{count:04d}"
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    """Model for individual items in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.inventory.medicine.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class SaleReturn(models.Model):
    """Model for sale returns"""
    RETURN_REASONS = [
        ('EXPIRED', 'Expired Medicine'),
        ('DAMAGED', 'Damaged Product'),
        ('WRONG_ITEM', 'Wrong Item'),
        ('CUSTOMER_REQUEST', 'Customer Request'),
        ('OTHER', 'Other'),
    ]
    
    original_sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    return_number = models.CharField(max_length=100, unique=True)
    reason = models.CharField(max_length=20, choices=RETURN_REASONS)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Return {self.return_number} for Sale {self.original_sale.sale_number}"
    
    def save(self, *args, **kwargs):
        if not self.return_number:
            # Generate return number
            from django.utils import timezone
            today = timezone.now().date()
            count = SaleReturn.objects.filter(created_at__date=today).count() + 1
            self.return_number = f"RET-{today.strftime('%Y%m%d')}-{count:04d}"
        super().save(*args, **kwargs)


class SaleReturnItem(models.Model):
    """Model for individual items in a sale return"""
    sale_return = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.CASCADE)
    return_quantity = models.PositiveIntegerField()
    return_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"Return {self.sale_item.inventory.medicine.name} x {self.return_quantity}"