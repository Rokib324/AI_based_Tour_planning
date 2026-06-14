from django.contrib import admin
from .models import Destination, TourPackage, CustomTour, ItineraryItem, ApprovalLog

class ItineraryItemInline(admin.TabularInline):
    model = ItineraryItem
    extra = 1

class CustomTourAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'status', 'total_price', 'start_date', 'end_date', 'assigned_manager', 'assigned_approver']
    list_filter = ['status', 'start_date']
    search_fields = ['title', 'client__username']
    inlines = [ItineraryItemInline]

class TourPackageAdmin(admin.ModelAdmin):
    list_display = ['title', 'duration_days', 'price', 'is_active', 'created_by']
    inlines = [ItineraryItemInline]

admin.site.register(Destination)
admin.site.register(TourPackage, TourPackageAdmin)
admin.site.register(CustomTour, CustomTourAdmin)
admin.site.register(ItineraryItem)
admin.site.register(ApprovalLog)

