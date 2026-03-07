from rest_framework import serializers

from apps.pos.models import POSSession, CashDrawerLog


class POSSessionSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    cash_difference = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = POSSession
        fields = [
            'id', 'restaurant', 'staff', 'staff_name',
            'opened_at', 'closed_at', 'opening_cash', 'closing_cash',
            'expected_cash', 'is_active', 'notes', 'cash_difference',
        ]
        read_only_fields = [
            'id', 'restaurant', 'staff', 'opened_at', 'closed_at', 'is_active',
        ]


class CashDrawerLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashDrawerLog
        fields = ['id', 'pos_session', 'log_type', 'amount', 'note', 'created_at']
        read_only_fields = ['id', 'pos_session', 'created_at']
