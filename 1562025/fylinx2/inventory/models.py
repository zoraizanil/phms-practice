from django.db import models
from django.conf import settings
from pharmacies.models import Pharmacy


class Medicine(models.Model):
    """Model for medicine/drug information"""
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dosage_form = models.CharField(max_length=100)  # tablet, capsule, syrup, etc.
    strength = models.CharField(max_length=100)  # 500mg, 10ml, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'manufacturer', 'strength']
    
    def __str__(self):
        return f"{self.name} ({self.strength}) - {self.manufacturer}"


class Inventory(models.Model):
    """Model for pharmacy inventory"""
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='inventory_items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    manufacture_date = models.DateField()
    supplier = models.CharField(max_length=255)
    minimum_stock_level = models.PositiveIntegerField(default=10)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['pharmacy', 'medicine', 'batch_number']
    
    def __str__(self):
        return f"{self.medicine.name} - {self.pharmacy.name} (Batch: {self.batch_number})"
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock_level
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()


class StockMovement(models.Model):
    """Model for tracking stock movements"""
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
    ]
    
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Can be negative for OUT movements
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.movement_type} - {self.inventory.medicine.name} ({self.quantity})"