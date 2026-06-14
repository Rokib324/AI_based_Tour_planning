import json
from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ai_service.gemini_client import audit_itinerary_feasibility
from .models import Destination, TourPackage, CustomTour, ItineraryItem, ApprovalLog
from .serializers import (
    DestinationSerializer, TourPackageSerializer, CustomTourSerializer,
    ItineraryItemSerializer, ApprovalLogSerializer
)

class IsAdminOrManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (request.user.role in ['admin', 'tour_manager'] or request.user.is_superuser)

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

class TourPackageViewSet(viewsets.ModelViewSet):
    queryset = TourPackage.objects.all()
    serializer_class = TourPackageSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class CustomTourViewSet(viewsets.ModelViewSet):
    serializer_class = CustomTourSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return CustomTour.objects.none()
        if user.is_superuser or user.role == 'admin':
            return CustomTour.objects.all()
        if user.role == 'tour_manager':
            return CustomTour.objects.exclude(status='draft')
        if user.role == 'financial_approver':
            return CustomTour.objects.filter(status__in=['pending_finance', 'approved', 'paid', 'cancelled'])
        return CustomTour.objects.filter(client=user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'client' and instance.status != 'draft':
            return Response(
                {"detail": "You cannot delete a tour that has been submitted for review."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'client' and instance.status not in ['draft', 'rejected']:
            return Response(
                {"detail": "You can only edit tours in draft or rejected status."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_tour(self, request, pk=None):
        tour = self.get_object()
        if tour.client != request.user and not request.user.is_superuser:
            return Response({"detail": "You do not own this tour."}, status=status.HTTP_403_FORBIDDEN)
            
        if tour.status not in ['draft', 'rejected']:
            return Response({"detail": "You can only submit draft or rejected tours."}, status=status.HTTP_400_BAD_REQUEST)

        # Run AI Feasibility Audit
        items_data = []
        for item in tour.itinerary_items.all():
            items_data.append({
                'day_number': item.day_number,
                'activity_title': item.activity_title,
                'activity_description': item.activity_description,
                'estimated_cost': float(item.estimated_cost)
            })
            
        duration = (tour.end_date - tour.start_date).days + 1
        audit_res = audit_itinerary_feasibility(tour.title, duration, items_data)

        from_status = tour.status
        tour.ai_analysis = json.dumps(audit_res)
        tour.status = 'submitted_logistics'
        tour.save()

        ApprovalLog.objects.create(
            custom_tour=tour,
            acted_by=request.user,
            from_status=from_status,
            to_status='submitted_logistics',
            comments="Submitted for logistics review with AI audit."
        )

        return Response(CustomTourSerializer(tour).data)

    @action(detail=True, methods=['post'], url_path='manager-review')
    def manager_review(self, request, pk=None):
        tour = self.get_object()
        user = request.user
        
        if user.role not in ['tour_manager', 'admin'] and not user.is_superuser:
            return Response({"detail": "Only tour managers or admins can review logistics."}, status=status.HTTP_403_FORBIDDEN)
            
        if tour.status != 'submitted_logistics':
            return Response({"detail": "Tour is not in submitted_logistics state."}, status=status.HTTP_400_BAD_REQUEST)
            
        action_type = request.data.get('action')
        comments = request.data.get('comments', '')
        markup_amount = request.data.get('markup_amount')
        
        if action_type not in ['approve', 'reject']:
            return Response({"detail": "action must be 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)
            
        if action_type == 'reject' and not comments:
            return Response({"detail": "Comments are required when rejecting a tour."}, status=status.HTTP_400_BAD_REQUEST)
            
        from_status = tour.status
        if action_type == 'approve':
            tour.status = 'pending_finance'
            tour.assigned_manager = user
            if markup_amount is not None:
                try:
                    tour.markup_amount = Decimal(str(markup_amount))
                except (ValueError, TypeError):
                    return Response({"detail": "Invalid markup amount."}, status=status.HTTP_400_BAD_REQUEST)
            tour.recalculate_prices()
            to_status = 'pending_finance'
        else:
            tour.status = 'rejected'
            to_status = 'rejected'
            
        tour.save()
        
        ApprovalLog.objects.create(
            custom_tour=tour,
            acted_by=user,
            from_status=from_status,
            to_status=to_status,
            comments=comments
        )
        
        return Response(CustomTourSerializer(tour).data)

    @action(detail=True, methods=['post'], url_path='finance-review')
    def finance_review(self, request, pk=None):
        tour = self.get_object()
        user = request.user
        
        if user.role not in ['financial_approver', 'admin'] and not user.is_superuser:
            return Response({"detail": "Only financial approvers or admins can perform financial review."}, status=status.HTTP_403_FORBIDDEN)
            
        if tour.status != 'pending_finance':
            return Response({"detail": "Tour is not in pending_finance state."}, status=status.HTTP_400_BAD_REQUEST)
            
        action_type = request.data.get('action')
        comments = request.data.get('comments', '')
        
        if action_type not in ['approve', 'reject']:
            return Response({"detail": "action must be 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)
            
        if action_type == 'reject' and not comments:
            return Response({"detail": "Comments are required when rejecting a tour."}, status=status.HTTP_400_BAD_REQUEST)
            
        from_status = tour.status
        if action_type == 'approve':
            tour.status = 'approved'
            tour.assigned_approver = user
            to_status = 'approved'
        else:
            tour.status = 'rejected'
            to_status = 'rejected'
            
        tour.save()
        
        ApprovalLog.objects.create(
            custom_tour=tour,
            acted_by=user,
            from_status=from_status,
            to_status=to_status,
            comments=comments
        )
        
        return Response(CustomTourSerializer(tour).data)

    @action(detail=True, methods=['get'], url_path='logs')
    def logs(self, request, pk=None):
        tour = self.get_object()
        logs = tour.approval_logs.all().order_by('-created_at')
        serializer = ApprovalLogSerializer(logs, many=True)
        return Response(serializer.data)


