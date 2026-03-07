import random

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Order(TimeStampedModel):
    """Customer order — created via QR scan or POS."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PREPARING = 'preparing', 'Preparing'
        READY = 'ready', 'Ready'
        SERVED = 'served', 'Served'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    class OrderType(models.TextChoices):
        DINE_IN = 'dine_in', 'Dine In'
        TAKEAWAY = 'takeaway', 'Takeaway'
        DELIVERY = 'delivery', 'Delivery'

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE, related_name='orders'
    )
    table = models.ForeignKey(
        'tenants.Table', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders'
    )
    table_session = models.ForeignKey(
        'tenants.TableSession', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders'
    )
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    order_type = models.CharField(
        max_length=20, choices=OrderType.choices, default=OrderType.DINE_IN
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Financials
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    deal = models.ForeignKey(
        'menu.Deal', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders'
    )
    special_instructions = models.TextField(blank=True)

    # Who created this — staff (POS) or null (customer self-order)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_orders'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['restaurant', '-created_at']),
            models.Index(fields=['table', 'status']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def _generate_order_number(self):
        date_str = timezone.now().strftime('%Y%m%d')
        random_part = random.randint(1000, 9999)
        return f"ORD-{date_str}-{random_part}"

    def calculate_totals(self):
        """Recalculate all financial fields from order items."""
        self.subtotal = sum(item.subtotal for item in self.items.all())
        self.tax_amount = self.subtotal * (self.restaurant.tax_rate / 100)
        self.service_charge = self.subtotal * (self.restaurant.service_charge_rate / 100)
        self.total = (
            self.subtotal + self.tax_amount + self.service_charge - self.discount_amount
        )
        self.save(update_fields=[
            'subtotal', 'tax_amount', 'service_charge', 'total', 'updated_at'
        ])


class OrderItem(TimeStampedModel):
    """Individual item within an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.CASCADE)
    variant = models.ForeignKey(
        'menu.MenuItemVariant', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.TextField(blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if not self.unit_price:
            if self.variant:
                self.unit_price = self.variant.total_price
            else:
                self.unit_price = self.menu_item.price
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def recalculate_with_modifiers(self):
        """Call after adding modifiers to recalculate subtotal."""
        modifier_total = sum(m.price for m in self.modifiers.all())
        self.subtotal = (self.unit_price + modifier_total) * self.quantity
        self.save(update_fields=['subtotal', 'updated_at'])


class OrderItemModifier(models.Model):
    """Modifier applied to a specific order item."""
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name='modifiers'
    )
    modifier = models.ForeignKey('menu.Modifier', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.modifier.name} (+Rs.{self.price})"

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.modifier.price
        super().save(*args, **kwargs)
