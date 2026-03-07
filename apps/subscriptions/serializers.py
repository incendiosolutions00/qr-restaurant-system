from rest_framework import serializers

from apps.subscriptions.models import Plan, Subscription, SubscriptionPayment


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'description', 'price', 'billing_cycle',
            'max_tables', 'max_menu_items', 'max_staff_accounts',
            'max_orders_per_month',
            'has_pos', 'has_kitchen_display', 'has_reports',
            'has_deals', 'has_online_payment',
            'is_active', 'display_order',
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'restaurant', 'plan', 'plan_name', 'status',
            'start_date', 'end_date', 'trial_end', 'auto_renew',
            'is_valid', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPayment
        fields = [
            'id', 'subscription', 'amount', 'payment_date',
            'payment_method', 'transaction_id', 'status',
        ]
        read_only_fields = ['id']
