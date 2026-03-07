from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    """Menu category (e.g. Appetizers, Main Course, Desserts)."""
    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE,
        related_name='menu_categories'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='menu/categories/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']
        unique_together = ['restaurant', 'name']

    def __str__(self):
        return f"{self.name} — {self.restaurant.name}"


class MenuItem(TimeStampedModel):
    """Individual dish or drink on the menu."""
    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE,
        related_name='menu_items'
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='items'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu/items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    prep_time = models.PositiveIntegerField(
        help_text='Preparation time in minutes', default=15
    )
    display_order = models.PositiveIntegerField(default=0)
    modifier_groups = models.ManyToManyField(
        'ModifierGroup', blank=True, related_name='menu_items'
    )

    class Meta:
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['restaurant', 'category', 'is_available']),
        ]

    def __str__(self):
        return f"{self.name} — Rs.{self.price}"


class MenuItemVariant(TimeStampedModel):
    """Size / variant of a menu item (e.g. Small, Medium, Large)."""
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.CASCADE, related_name='variants'
    )
    name = models.CharField(max_length=100)
    price_adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text='Added to base price (+/-)'
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['menu_item', 'name']

    def __str__(self):
        return f"{self.menu_item.name} — {self.name}"

    @property
    def total_price(self):
        return self.menu_item.price + self.price_adjustment


class ModifierGroup(TimeStampedModel):
    """Group of modifiers (e.g. "Choose Sauce", "Extra Toppings")."""
    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE,
        related_name='modifier_groups'
    )
    name = models.CharField(max_length=100)
    is_required = models.BooleanField(default=False)
    min_selections = models.PositiveIntegerField(default=0)
    max_selections = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.name} — {self.restaurant.name}"


class Modifier(TimeStampedModel):
    """Individual modifier option (e.g. Extra Cheese +Rs.50)."""
    group = models.ForeignKey(
        ModifierGroup, on_delete=models.CASCADE, related_name='modifiers'
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        if self.price > 0:
            return f"{self.name} (+Rs.{self.price})"
        return self.name


class Deal(TimeStampedModel):
    """Special deals / combos offered by the restaurant."""

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage'
        FLAT = 'flat', 'Flat Amount'
        FIXED_PRICE = 'fixed_price', 'Fixed Combo Price'

    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE,
        related_name='deals'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='menu/deals/', blank=True, null=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date


class DealItem(models.Model):
    """Items included in a deal."""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['deal', 'menu_item']

    def __str__(self):
        return f"{self.deal.name} — {self.menu_item.name} x{self.quantity}"
