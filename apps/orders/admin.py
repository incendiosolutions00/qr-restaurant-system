from django.contrib import admin

from apps.orders.models import Order, OrderItem, OrderItemModifier


class OrderItemModifierInline(admin.TabularInline):
    model = OrderItemModifier
    extra = 0
    readonly_fields = ['modifier', 'price']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['menu_item', 'variant', 'quantity', 'unit_price', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'restaurant', 'table', 'order_type',
        'status', 'total', 'created_at',
    ]
    list_filter = ['status', 'order_type', 'restaurant', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'variant', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['order__restaurant']
    inlines = [OrderItemModifierInline]
