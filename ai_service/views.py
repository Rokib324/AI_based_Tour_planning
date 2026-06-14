# pyrefly: ignore [missing-import]
from rest_framework.views import APIView
# pyrefly: ignore [missing-import]
from rest_framework.response import Response
# pyrefly: ignore [missing-import]
from rest_framework import permissions, status
from .gemini_client import generate_itinerary, audit_itinerary_feasibility

class GenerateItineraryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        destination = request.data.get('destination')
        budget = request.data.get('budget')
        duration_days = request.data.get('duration_days')
        interests = request.data.get('interests', 'general')

        if not destination or not budget or not duration_days:
            return Response(
                {"detail": "destination, budget, and duration_days are required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            duration_days = int(duration_days)
            if duration_days <= 0:
                raise ValueError
        except ValueError:
            return Response(
                {"detail": "duration_days must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        itinerary = generate_itinerary(destination, budget, duration_days, interests)
        return Response(itinerary, status=status.HTTP_200_OK)

class AuditItineraryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        title = request.data.get('title', 'Custom Tour')
        duration_days = request.data.get('duration_days')
        itinerary_items = request.data.get('itinerary_items')

        if not duration_days or itinerary_items is None:
            return Response(
                {"detail": "duration_days and itinerary_items are required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            duration_days = int(duration_days)
            if duration_days <= 0:
                raise ValueError
        except ValueError:
            return Response(
                {"detail": "duration_days must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(itinerary_items, list):
            return Response(
                {"detail": "itinerary_items must be a list of activity objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        audit_result = audit_itinerary_feasibility(title, duration_days, itinerary_items)
        return Response(audit_result, status=status.HTTP_200_OK)

