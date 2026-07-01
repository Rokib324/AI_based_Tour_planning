# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    path('generate-itinerary/', views.GenerateItineraryView.as_view(), name='ai_generate_itinerary'),
    path('audit-feasibility/', views.AuditItineraryView.as_view(), name='ai_audit_feasibility'),
]
