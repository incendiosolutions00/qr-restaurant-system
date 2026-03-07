from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrAbove, IsStaffOrAbove
from apps.orders.models import Order
from apps.payments.models import Payment, Refund
from apps.payments.serializers import (
    CashPaymentSerializer, PaymentSerializer, RefundSerializer,
)


class PaymentListView(generics.ListAPIView):
    """List payments for the restaurant."""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]
    filterset_fields = ['method', 'status']

    def get_queryset(self):
        return Payment.objects.filter(
            order__restaurant=self.request.user.restaurant,
        ).select_related('order')


class PaymentDetailView(generics.RetrieveAPIView):
    """View a single payment."""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAbove]

    def get_queryset(self):
        return Payment.objects.filter(
            order__restaurant=self.request.user.restaurant,
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsStaffOrAbove])
@transaction.atomic
def process_cash_payment(request):
    """POS — process a cash payment for an order."""
    serializer = CashPaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        order = Order.objects.get(
            pk=serializer.validated_data['order_id'],
            restaurant=request.user.restaurant,
        )
    except Order.DoesNotExist:
        return Response(
            {'detail': 'Order not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    amount_received = serializer.validated_data['amount_received']
    if amount_received < order.total:
        return Response(
            {'detail': f'Amount received (Rs.{amount_received}) is less than total (Rs.{order.total}).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    import uuid
    payment = Payment.objects.create(
        order=order,
        method=Payment.Method.CASH,
        amount=order.total,
        status=Payment.Status.COMPLETED,
        amount_received=amount_received,
        change_amount=amount_received - order.total,
        transaction_id=f"CASH-{uuid.uuid4().hex[:12].upper()}",
        processed_by=request.user,
    )

    order.status = Order.Status.COMPLETED
    order.save(update_fields=['status', 'updated_at'])

    return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsStaffOrAbove])
@transaction.atomic
def process_card_payment(request):
    """POS — record a card payment for an order."""
    order_id = request.data.get('order_id')
    try:
        order = Order.objects.get(
            pk=order_id, restaurant=request.user.restaurant,
        )
    except Order.DoesNotExist:
        return Response(
            {'detail': 'Order not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    import uuid
    payment = Payment.objects.create(
        order=order,
        method=Payment.Method.CARD,
        amount=order.total,
        status=Payment.Status.COMPLETED,
        transaction_id=f"CARD-{uuid.uuid4().hex[:12].upper()}",
        processed_by=request.user,
    )

    order.status = Order.Status.COMPLETED
    order.save(update_fields=['status', 'updated_at'])

    return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


# ─── REFUNDS ────────────────────────────────────────────────────────────────

class RefundCreateView(generics.CreateAPIView):
    """Manager — issue a refund against a payment."""
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def perform_create(self, serializer):
        refund = serializer.save(processed_by=self.request.user)
        # Update payment status
        payment = refund.payment
        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=['status', 'updated_at'])
