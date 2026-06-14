from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('tour_manager', 'Tour Manager'),
        ('financial_approver', 'Financial Approver'),
        ('admin', 'Admin'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    def is_client(self):
        return self.role == 'client'
        
    def is_tour_manager(self):
        return self.role == 'tour_manager'
        
    def is_financial_approver(self):
        return self.role == 'financial_approver'

    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

