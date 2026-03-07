from rest_framework import serializers

from apps.orders.models import Order, OrderItem, OrderItemModifier


class OrderItemModifierSerializer(serializers.ModelSerializer):
    modifier_name = serializers.CharField(source='modifier.name', read_only=True)

    class Meta:
        model = OrderItemModifier
        fields = ['id', 'modifier', 'modifier_name', 'price']
        read_only_fields = ['id', 'price']


class OrderItemSerializer(serializers.ModelSerializer):
    modifiers = OrderItemModifierSerializer(many=True, read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, default=None)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'menu_item_name', 'variant', 'variant_name',
            'quantity', 'unit_price', 'subtotal', 'special_instructions',
            'modifiers',
        ]
        read_only_fields = ['id', 'unit_price', 'subtotal']


class OrderItemCreateSerializer(serializers.Serializer):
    """For creating order items within an order."""
    menu_item_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)
    special_instructions = serializers.CharField(required=False, default='')
    modifier_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=[]
    )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    table_number = serializers.IntegerField(source='table.number', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'restaurant', 'table', 'table_number',
            'table_session', 'customer_name', 'customer_phone',
            'order_type', 'status', 'status_display',
            'subtotal', 'tax_amount', 'service_charge',
            'discount_amount', 'total', 'deal',
            'special_instructions', 'created_by',
            'items', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'order_number', 'restaurant', 'subtotal', 'tax_amount',
            'service_charge', 'total', 'created_by', 'created_at', 'updated_at',
        ]


class CustomerOrderCreateSerializer(serializers.Serializer):
    """Customer placing an order after scanning QR."""
    table_id = serializers.IntegerField()
    session_id = serializers.UUIDField(required=False)
    customer_name = serializers.CharField(max_length=100, required=False, default='')
    customer_phone = serializers.CharField(max_length=20, required=False, default='')
    order_type = serializers.ChoiceField(
        choices=Order.OrderType.choices, default='dine_in'
    )
    special_instructions = serializers.CharField(required=False, default='')
    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('Order must have at least one item.')
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    """For staff to update order status."""
    status = serializers.ChoiceField(choices=Order.Status.choices)
