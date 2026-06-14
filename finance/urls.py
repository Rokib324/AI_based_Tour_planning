# pyrefly: ignore [missing-import]
from django.urls import path
from .views import CheckoutView, MockPaymentView, TransactionListView, DashboardAnalyticsView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='finance_checkout'),
    path('mock-pay/', MockPaymentView.as_view(), name='finance_mock_pay'),
    path('transactions/', TransactionListView.as_view(), name='finance_transactions'),
    path('analytics/', DashboardAnalyticsView.as_view(), name='finance_analytics'),
]
