# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('STAFF', 'Staff'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True, blank=True)

    assigned_pharmacy = models.ForeignKey(
        'pharmacies.Pharmacy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_users'
    )

    # ❌ Remove this line (it clashes with Pharmacy.managers related_name)
    # managed_pharmacies = models.ManyToManyField('pharmacies.Pharmacy', blank=True)

    def __str__(self):
        return f"{self.username} ({self.role if self.role else 'Superuser'})"
