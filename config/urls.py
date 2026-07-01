"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# pyrefly: ignore [missing-import]
from django.contrib import admin
# pyrefly: ignore [missing-import]
from django.urls import path, include
# pyrefly: ignore [missing-import]
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='landing.html'), name='home'),

    # Auth pages
    path('auth/login/', TemplateView.as_view(template_name='auth/login.html'), name='page_login'),
    path('auth/register/', TemplateView.as_view(template_name='auth/register.html'), name='page_register'),
    path('auth/forgot-password/', TemplateView.as_view(template_name='auth/forgot-password.html'), name='page_forgot_password'),
    path('auth/reset-password/', TemplateView.as_view(template_name='auth/reset-password.html'), name='page_reset_password'),
    path('auth/verify-email/', TemplateView.as_view(template_name='auth/verify-email.html'), name='page_verify_email'),

    # Role-based dashboards
    path('dashboard/', TemplateView.as_view(template_name='dashboard/index.html'), name='dashboard'),
    path('dashboard/client/', TemplateView.as_view(template_name='dashboard/client.html'), name='dashboard_client'),
    path('dashboard/manager/', TemplateView.as_view(template_name='dashboard/tour_manager.html'), name='dashboard_manager'),
    path('dashboard/finance/', TemplateView.as_view(template_name='dashboard/financial_approver.html'), name='dashboard_finance'),
    path('dashboard/admin/', TemplateView.as_view(template_name='dashboard/admin.html'), name='dashboard_admin'),
    path('dashboard/planner/', TemplateView.as_view(template_name='dashboard/travel_planner.html'), name='travel_planner'),


    path('api/users/', include('users.urls')),
    path('api/tours/', include('tours.urls')),
    path('api/ai/', include('ai_service.urls')),
    path('api/finance/', include('finance.urls')),
]
