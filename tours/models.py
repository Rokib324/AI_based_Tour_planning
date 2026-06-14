from django.db import models
from django.conf import settings
from decimal import Decimal

class Destination(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    average_daily_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name}, {self.country}"

class TourPackage(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_days = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_packages'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class CustomTour(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted_logistics', 'Submitted for Logistics Review'),
        ('pending_finance', 'Pending Financial Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_tours'
    )
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    
    assigned_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_logistics_tours'
    )
    assigned_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_finance_tours'
    )

    base_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    markup_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=50.00)
    
    ai_analysis = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recalculate_prices(self):
        base = sum(Decimal(str(item.estimated_cost)) for item in self.itinerary_items.all())
        self.base_cost = base
        self.total_price = self.base_cost + Decimal(str(self.service_fee)) + Decimal(str(self.markup_amount))

    def save(self, *args, **kwargs):
        self.base_cost = Decimal(str(self.base_cost))
        self.service_fee = Decimal(str(self.service_fee))
        self.markup_amount = Decimal(str(self.markup_amount))
        self.total_price = self.base_cost + self.service_fee + self.markup_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.client.username} ({self.get_status_display()})"

class ItineraryItem(models.Model):
    tour_package = models.ForeignKey(
        TourPackage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='itinerary_items'
    )
    custom_tour = models.ForeignKey(
        CustomTour,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='itinerary_items'
    )
    day_number = models.IntegerField()
    activity_title = models.CharField(max_length=200)
    activity_description = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['day_number']

    def __str__(self):
        tour_name = self.tour_package.title if self.tour_package else self.custom_tour.title
        return f"Day {self.day_number}: {self.activity_title} ({tour_name})"

class ApprovalLog(models.Model):
    custom_tour = models.ForeignKey(
        CustomTour,
        on_delete=models.CASCADE,
        related_name='approval_logs'
    )
    acted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.custom_tour.title}: {self.from_status} -> {self.to_status} by {self.acted_by.username if self.acted_by else 'System'}"

