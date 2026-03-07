from rest_framework import serializers

from apps.reports.models import DailySummary


class DailySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySummary
        fields = [
            'id', 'restaurant', 'date',
            'total_orders', 'completed_orders', 'cancelled_orders',
            'gross_revenue', 'tax_collected', 'service_charges',
            'discounts_given', 'net_revenue', 'avg_order_value',
            'top_selling_items', 'payment_method_breakdown',
            'hourly_order_counts',
        ]
        read_only_fields = fields


class DashboardSerializer(serializers.Serializer):
    """Dashboard overview stats."""
    todays_orders = serializers.IntegerField()
    todays_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_orders = serializers.IntegerField()
    active_tables = serializers.IntegerField()
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_items_today = serializers.ListField()
