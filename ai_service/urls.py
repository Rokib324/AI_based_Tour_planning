# pyrefly: ignore [missing-import]
from django.urls import path
from .views import GenerateItineraryView, AuditItineraryView

urlpatterns = [
    path('generate-itinerary/', GenerateItineraryView.as_view(), name='ai_generate_itinerary'),
    path('audit-feasibility/', AuditItineraryView.as_view(), name='ai_audit_feasibility'),
]
