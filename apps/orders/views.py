from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsKitchenStaff, IsRestaurantMember
from apps.menu.models import MenuItem, MenuItemVariant, Modifier
from apps.orders.models import Order, OrderItem, OrderItemModifier
from apps.orders.serializers import (
    CustomerOrderCreateSerializer, OnlineOrderCreateSerializer,
    OrderSerializer, OrderStatusUpdateSerializer,
)
from apps.tenants.models import Restaurant, Table, TableSession


# ─── CUSTOMER ORDER PLACEMENT ───────────────────────────────────────────────

class CustomerPlaceOrderView(generics.CreateAPIView):
    """Public — customer places an order after scanning QR."""
    serializer_class = CustomerOrderCreateSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def create(self, request, slug, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Validate restaurant
        try:
            restaurant = Restaurant.objects.get(
                slug=slug, is_active=True, is_approved=True
            )
        except Restaurant.DoesNotExist:
            return Response(
                {'detail': 'Restaurant not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if restaurant is open
        if not restaurant.is_open:
            reason = restaurant.closure_status.get('reason', 'Restaurant is currently closed.')
            return Response({'detail': reason}, status=status.HTTP_400_BAD_REQUEST)

        # Validate table
        try:
            table = Table.objects.get(
                pk=data['table_id'], restaurant=restaurant, is_active=True
            )
        except Table.DoesNotExist:
            return Response(
                {'detail': 'Table not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get or create session
        session = None
        if data.get('session_id'):
            session = TableSession.objects.filter(
                session_id=data['session_id'], is_active=True
            ).first()
        if not session:
            session, _ = TableSession.objects.get_or_create(
                table=table, is_active=True,
                defaults={'guest_count': 1}
            )
            table.status = Table.Status.OCCUPIED
            table.save(update_fields=['status', 'updated_at'])

        # Create order
        order = Order.objects.create(
            restaurant=restaurant,
            table=table,
            table_session=session,
            customer_name=data.get('customer_name', ''),
            customer_phone=data.get('customer_phone', ''),
            order_type=data.get('order_type', 'dine_in'),
            special_instructions=data.get('special_instructions', ''),
        )

        # Create order items
        for item_data in data['items']:
            menu_item = MenuItem.objects.get(
                pk=item_data['menu_item_id'], restaurant=restaurant
            )

            variant = None
            if item_data.get('variant_id'):
                variant = MenuItemVariant.objects.get(
                    pk=item_data['variant_id'], menu_item=menu_item
                )

            unit_price = variant.total_price if variant else menu_item.price

            order_item = OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                variant=variant,
                quantity=item_data.get('quantity', 1),
                unit_price=unit_price,
                subtotal=unit_price * item_data.get('quantity', 1),
                special_instructions=item_data.get('special_instructions', ''),
            )

            # Add modifiers
            for mod_id in item_data.get('modifier_ids', []):
                modifier = Modifier.objects.get(pk=mod_id)
                OrderItemModifier.objects.create(
                    order_item=order_item,
                    modifier=modifier,
                    price=modifier.price,
                )

            # Recalculate with modifiers
            if item_data.get('modifier_ids'):
                order_item.recalculate_with_modifiers()

        # Calculate totals
        order.calculate_totals()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class CustomerOrderStatusView(generics.RetrieveAPIView):
    """Public — customer checks their order status."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(
            restaurant__slug=self.kwargs['slug'],
        ).prefetch_related('items__modifiers')


class OnlineOrderView(generics.CreateAPIView):
    """Public — customer places a delivery/takeaway order online (no QR scan)."""
    serializer_class = OnlineOrderCreateSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def create(self, request, slug, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            restaurant = Restaurant.objects.get(
                slug=slug, is_active=True, is_approved=True
            )
        except Restaurant.DoesNotExist:
            return Response(
                {'detail': 'Restaurant not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not restaurant.is_open:
            reason = restaurant.closure_status.get('reason', 'Restaurant is currently closed.')
            return Response({'detail': reason}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(
            restaurant=restaurant,
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            delivery_address=data.get('delivery_address', ''),
            order_type=data['order_type'],
            special_instructions=data.get('special_instructions', ''),
        )

        for item_data in data['items']:
            menu_item = MenuItem.objects.get(
                pk=item_data['menu_item_id'], restaurant=restaurant
            )
            variant = None
            if item_data.get('variant_id'):
                variant = MenuItemVariant.objects.get(
                    pk=item_data['variant_id'], menu_item=menu_item
                )
            unit_price = variant.total_price if variant else menu_item.price
            order_item = OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                variant=variant,
                quantity=item_data.get('quantity', 1),
                unit_price=unit_price,
                subtotal=unit_price * item_data.get('quantity', 1),
                special_instructions=item_data.get('special_instructions', ''),
            )
            for mod_id in item_data.get('modifier_ids', []):
                modifier = Modifier.objects.get(pk=mod_id)
                OrderItemModifier.objects.create(
                    order_item=order_item,
                    modifier=modifier,
                    price=modifier.price,
                )
            if item_data.get('modifier_ids'):
                order_item.recalculate_with_modifiers()

        order.calculate_totals()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


# ─── RESTAURANT STAFF — ORDER MANAGEMENT ────────────────────────────────────

class OrderListView(generics.ListAPIView):
    """Staff — list orders for their restaurant."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantMember]
    filterset_fields = ['status', 'order_type', 'table']
    search_fields = ['order_number', 'customer_name']

    def get_queryset(self):
        return Order.objects.filter(
            restaurant=self.request.user.restaurant
        ).select_related('table', 'table_session').prefetch_related(
            'items__menu_item', 'items__modifiers__modifier'
        )


class OrderDetailView(generics.RetrieveAPIView):
    """Staff — view single order detail."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantMember]

    def get_queryset(self):
        return Order.objects.filter(
            restaurant=self.request.user.restaurant
        ).prefetch_related('items__menu_item', 'items__modifiers__modifier')


class ActiveOrdersView(generics.ListAPIView):
    """Staff / Kitchen — list all active (non-completed, non-cancelled) orders."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantMember]

    def get_queryset(self):
        return Order.objects.filter(
            restaurant=self.request.user.restaurant,
            status__in=['pending', 'confirmed', 'preparing', 'ready', 'served'],
        ).select_related('table').prefetch_related(
            'items__menu_item', 'items__modifiers__modifier'
        )


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated, IsRestaurantMember])
def update_order_status(request, pk):
    """Staff — update order status (pending -> confirmed -> preparing -> etc.)."""
    try:
        order = Order.objects.get(pk=pk, restaurant=request.user.restaurant)
    except Order.DoesNotExist:
        return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = OrderStatusUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    new_status = serializer.validated_data['status']
    order.status = new_status
    order.save(update_fields=['status', 'updated_at'])

    return Response(OrderSerializer(order).data)


# ─── KITCHEN VIEW ────────────────────────────────────────────────────────────

class KitchenOrdersView(generics.ListAPIView):
    """Kitchen display — orders that need to be prepared."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            restaurant=self.request.user.restaurant,
            status__in=['confirmed', 'preparing'],
        ).select_related('table').prefetch_related(
            'items__menu_item', 'items__variant', 'items__modifiers__modifier'
        ).order_by('created_at')
