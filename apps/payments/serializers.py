from rest_framework import serializers

from apps.payments.models import Payment, Refund


class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'method', 'method_display', 'amount',
            'status', 'status_display', 'transaction_id',
            'amount_received', 'change_amount',
            'processed_by', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'transaction_id',
            'change_amount', 'processed_by', 'created_at', 'updated_at',
        ]


class CashPaymentSerializer(serializers.Serializer):
    """Process a cash payment at POS."""
    order_id = serializers.IntegerField()
    amount_received = serializers.DecimalField(max_digits=10, decimal_places=2)


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'reason',
            'processed_by', 'transaction_id', 'created_at',
        ]
        read_only_fields = ['id', 'processed_by', 'transaction_id', 'created_at']
