from django.db import models

from apps.core.models import TimeStampedModel


class Payment(TimeStampedModel):
    """Payment record for an order."""

    class Method(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Credit/Debit Card'
        ONLINE = 'online', 'Online Payment'
        JAZZCASH = 'jazzcash', 'JazzCash'
        EASYPAISA = 'easypaisa', 'EasyPaisa'
        STRIPE = 'stripe', 'Stripe'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE, related_name='payments'
    )
    method = models.CharField(max_length=20, choices=Method.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    transaction_id = models.CharField(
        max_length=200, blank=True, null=True, unique=True
    )

    # Cash-specific
    amount_received = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    change_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Gateway response storage
    gateway_response = models.JSONField(default=dict, blank=True)

    processed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='processed_payments'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
        ]

    def __str__(self):
        return f"Payment Rs.{self.amount} — {self.get_method_display()} ({self.get_status_display()})"

    def mark_completed(self, transaction_id=None):
        self.status = self.Status.COMPLETED
        if transaction_id:
            self.transaction_id = transaction_id
        self.save(update_fields=['status', 'transaction_id', 'updated_at'])
        # Mark the order as completed too
        self.order.status = 'completed'
        self.order.save(update_fields=['status', 'updated_at'])


class Refund(TimeStampedModel):
    """Refund against a completed payment."""
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='refunds'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    processed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True
    )
    transaction_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund Rs.{self.amount} — Payment #{self.payment_id}"
