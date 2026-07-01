from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random


def generate_otp():
    return str(random.randint(100000, 999999))


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('tour_manager', 'Tour Manager'),
        ('financial_approver', 'Financial Approver'),
        ('admin', 'Admin'),
    )

    PROVIDER_CHOICES = (
        ('email', 'Email'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
    )

    role            = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone_number    = models.CharField(max_length=15, blank=True, null=True)

    # Social auth provider
    social_provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='email')
    social_id       = models.CharField(max_length=200, blank=True, null=True, unique=True)

    # Email verification
    is_email_verified    = models.BooleanField(default=False)
    email_otp            = models.CharField(max_length=6, blank=True, null=True)
    email_otp_created_at = models.DateTimeField(blank=True, null=True)

    # Phone verification
    is_phone_verified    = models.BooleanField(default=False)
    phone_otp            = models.CharField(max_length=6, blank=True, null=True)
    phone_otp_created_at = models.DateTimeField(blank=True, null=True)

    # Password reset token (UUID stored as string)
    password_reset_token            = models.CharField(max_length=64, blank=True, null=True)
    password_reset_token_created_at = models.DateTimeField(blank=True, null=True)

    def set_email_otp(self):
        self.email_otp = generate_otp()
        self.email_otp_created_at = timezone.now()
        self.save(update_fields=['email_otp', 'email_otp_created_at'])
        return self.email_otp

    def set_phone_otp(self):
        self.phone_otp = generate_otp()
        self.phone_otp_created_at = timezone.now()
        self.save(update_fields=['phone_otp', 'phone_otp_created_at'])
        return self.phone_otp

    def is_email_otp_valid(self, otp, expiry_minutes=10):
        if not self.email_otp or not self.email_otp_created_at:
            return False
        age = (timezone.now() - self.email_otp_created_at).total_seconds() / 60
        return self.email_otp == otp and age <= expiry_minutes

    def is_phone_otp_valid(self, otp, expiry_minutes=10):
        if not self.phone_otp or not self.phone_otp_created_at:
            return False
        age = (timezone.now() - self.phone_otp_created_at).total_seconds() / 60
        return self.phone_otp == otp and age <= expiry_minutes

    def is_reset_token_valid(self, token, expiry_minutes=30):
        if not self.password_reset_token or not self.password_reset_token_created_at:
            return False
        age = (timezone.now() - self.password_reset_token_created_at).total_seconds() / 60
        return self.password_reset_token == token and age <= expiry_minutes

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
