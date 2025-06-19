# pharmacies/models.py
from django.db import models
from django.conf import settings  # use settings.AUTH_USER_MODEL

class Pharmacy(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_pharmacies'
    )
    is_superuser_created = models.BooleanField(default=False)

    # Assign multiple managers
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='managed_pharmacies',
        limit_choices_to={'role': 'MANAGER'}
    )

    def __str__(self):
        return self.name
    
