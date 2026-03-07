from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Plan(TimeStampedModel):
    """Subscription plans that super admin offers to restaurants."""

    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(
        max_length=20, choices=BillingCycle.choices, default=BillingCycle.MONTHLY
    )

    # Feature limits
    max_tables = models.PositiveIntegerField(default=10)
    max_menu_items = models.PositiveIntegerField(default=50)
    max_staff_accounts = models.PositiveIntegerField(default=5)
    max_orders_per_month = models.PositiveIntegerField(default=500)

    # Feature flags
    has_pos = models.BooleanField(default=False)
    has_kitchen_display = models.BooleanField(default=False)
    has_reports = models.BooleanField(default=False)
    has_deals = models.BooleanField(default=False)
    has_online_payment = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'price']

    def __str__(self):
        return f"{self.name} — Rs.{self.price}/{self.get_billing_cycle_display()}"


class Subscription(TimeStampedModel):
    """Restaurant's active subscription to a plan."""

    class Status(models.TextChoices):
        TRIAL = 'trial', 'Trial'
        ACTIVE = 'active', 'Active'
        PAST_DUE = 'past_due', 'Past Due'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'

    restaurant = models.OneToOneField(
        'tenants.Restaurant', on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name='subscriptions'
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TRIAL
    )
    start_date = models.DateField()
    end_date = models.DateField()
    trial_end = models.DateField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.restaurant.name} — {self.plan.name} ({self.get_status_display()})"

    @property
    def is_valid(self):
        today = timezone.now().date()
        return (
            self.status in [self.Status.TRIAL, self.Status.ACTIVE]
            and self.end_date >= today
        )


class SubscriptionPayment(TimeStampedModel):
    """Payment records for subscription billing."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Rs.{self.amount} — {self.subscription.restaurant.name}"
