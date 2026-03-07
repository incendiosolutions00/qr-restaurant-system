from django.db import models

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    """In-app notification for staff and customers."""

    class NotificationType(models.TextChoices):
        NEW_ORDER = 'new_order', 'New Order'
        ORDER_STATUS = 'order_status', 'Order Status Update'
        WAITER_CALL = 'waiter_call', 'Waiter Call'
        PAYMENT = 'payment', 'Payment'
        SYSTEM = 'system', 'System'

    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE,
        related_name='notifications'
    )
    recipient = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        null=True, blank=True, related_name='notifications'
    )
    target_role = models.CharField(
        max_length=20, blank=True,
        help_text='Broadcast to all users with this role'
    )
    notification_type = models.CharField(
        max_length=20, choices=NotificationType.choices
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'recipient', 'is_read']),
            models.Index(fields=['restaurant', 'target_role', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"


class WaiterCall(TimeStampedModel):
    """Customer presses 'Call Waiter' button from their table."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACKNOWLEDGED = 'acknowledged', 'Acknowledged'
        RESOLVED = 'resolved', 'Resolved'

    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE,
        related_name='waiter_calls'
    )
    table = models.ForeignKey(
        'tenants.Table', on_delete=models.CASCADE,
        related_name='waiter_calls'
    )
    table_session = models.ForeignKey(
        'tenants.TableSession', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    note = models.TextField(blank=True, help_text='Customer can add a note')
    responded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='responded_waiter_calls'
    )
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Waiter Call — Table {self.table.number} ({self.get_status_display()})"
