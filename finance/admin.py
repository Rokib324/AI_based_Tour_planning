from django.contrib import admin
from .models import Transaction

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'custom_tour', 'user', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['transaction_id', 'custom_tour__title', 'user__username']

admin.site.register(Transaction, TransactionAdmin)

