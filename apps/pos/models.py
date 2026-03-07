from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class POSSession(TimeStampedModel):
    """POS shift session — tracks cash drawer from open to close."""
    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE,
        related_name='pos_sessions'
    )
    staff = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='pos_sessions'
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    closing_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_cash = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-opened_at']
        verbose_name = 'POS Session'
        verbose_name_plural = 'POS Sessions'

    def __str__(self):
        return f"POS — {self.staff.get_full_name()} ({self.opened_at:%Y-%m-%d %H:%M})"

    def close_session(self, closing_cash=None):
        self.is_active = False
        self.closed_at = timezone.now()
        if closing_cash is not None:
            self.closing_cash = closing_cash
        self.save(update_fields=['is_active', 'closed_at', 'closing_cash', 'updated_at'])

    @property
    def cash_difference(self):
        if self.closing_cash is not None and self.expected_cash is not None:
            return self.closing_cash - self.expected_cash
        return None


class CashDrawerLog(TimeStampedModel):
    """Individual cash drawer transactions during a POS session."""

    class LogType(models.TextChoices):
        CASH_IN = 'cash_in', 'Cash In'
        CASH_OUT = 'cash_out', 'Cash Out'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    pos_session = models.ForeignKey(
        POSSession, on_delete=models.CASCADE, related_name='cash_logs'
    )
    log_type = models.CharField(max_length=20, choices=LogType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_log_type_display()} Rs.{self.amount}"
