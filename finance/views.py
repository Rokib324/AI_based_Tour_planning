import uuid
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from tours.models import CustomTour, ApprovalLog
from .models import Transaction
from .serializers import TransactionSerializer

class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        custom_tour_id = request.data.get('custom_tour_id')
        if not custom_tour_id:
            return Response({"detail": "custom_tour_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            tour = CustomTour.objects.get(id=custom_tour_id)
        except CustomTour.DoesNotExist:
            return Response({"detail": "Tour not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if tour.client != request.user and not request.user.is_superuser:
            return Response({"detail": "You do not own this tour request."}, status=status.HTTP_403_FORBIDDEN)
            
        if tour.status != 'approved':
            return Response({"detail": "Only approved tours can be processed for payment."}, status=status.HTTP_400_BAD_REQUEST)
            
        txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        transaction = Transaction.objects.create(
            custom_tour=tour,
            user=request.user,
            transaction_id=txn_id,
            amount=tour.total_price,
            payment_method='mock_gateway',
            status='pending'
        )
        
        gateway_url = f"/api/finance/mock-gateway/?txn_id={txn_id}"
        
        return Response({
            "detail": "Checkout created successfully.",
            "transaction": TransactionSerializer(transaction).data,
            "redirect_url": gateway_url
        }, status=status.HTTP_201_CREATED)

class MockPaymentView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        txn_id = request.data.get('transaction_id')
        payment_status = request.data.get('status')
        
        if not txn_id or payment_status not in ['success', 'failed']:
            return Response({"detail": "transaction_id and status ('success'/'failed') are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            txn = Transaction.objects.get(transaction_id=txn_id)
        except Transaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if txn.status != 'pending':
            return Response({"detail": "This transaction is already processed."}, status=status.HTTP_400_BAD_REQUEST)
            
        tour = txn.custom_tour
        
        if payment_status == 'success':
            txn.status = 'success'
            txn.save()
            
            from_status = tour.status
            tour.status = 'paid'
            tour.save()
            
            ApprovalLog.objects.create(
                custom_tour=tour,
                acted_by=txn.user,
                from_status=from_status,
                to_status='paid',
                comments=f"Mock payment of ${txn.amount} succeeded."
            )
            
            return Response({
                "detail": "Payment succeeded, tour status updated to paid.",
                "transaction_status": txn.status,
                "tour_status": tour.status
            })
        else:
            txn.status = 'failed'
            txn.save()
            
            return Response({
                "detail": "Payment failed, tour remains approved.",
                "transaction_status": txn.status,
                "tour_status": tour.status
            })

class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role in ['admin', 'financial_approver']:
            return Transaction.objects.all()
        return Transaction.objects.filter(user=user)

class DashboardAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.is_superuser or user.role in ['admin', 'tour_manager', 'financial_approver']:
            successful_txns = Transaction.objects.filter(status='success')
            total_revenue = sum(t.amount for t in successful_txns)
            
            paid_tours = CustomTour.objects.filter(status='paid')
            total_profit = sum(t.markup_amount for t in paid_tours)
            
            pending_logistics = CustomTour.objects.filter(status='submitted_logistics').count()
            pending_finance = CustomTour.objects.filter(status='pending_finance').count()
            approved_tours = CustomTour.objects.filter(status='approved').count()
            paid_count = paid_tours.count()
            
            status_breakdown = {}
            for status_code, status_label in CustomTour.STATUS_CHOICES:
                status_breakdown[status_code] = CustomTour.objects.filter(status=status_code).count()
                
            return Response({
                "scope": "global",
                "total_revenue": float(total_revenue),
                "total_profit": float(total_profit),
                "queue_size": {
                    "pending_logistics": pending_logistics,
                    "pending_finance": pending_finance
                },
                "status_breakdown": status_breakdown,
                "paid_tours_count": paid_count,
                "approved_tours_count": approved_tours
            })
        else:
            client_tours = CustomTour.objects.filter(client=user)
            total_spent = sum(t.amount for t in Transaction.objects.filter(user=user, status='success'))
            
            status_breakdown = {}
            for status_code, status_label in CustomTour.STATUS_CHOICES:
                status_breakdown[status_code] = client_tours.filter(status=status_code).count()
                
            return Response({
                "scope": "client",
                "total_spent": float(total_spent),
                "total_tours_count": client_tours.count(),
                "status_breakdown": status_breakdown
            })


