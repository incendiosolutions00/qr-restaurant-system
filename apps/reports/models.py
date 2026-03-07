from django.db import models

from apps.core.models import TimeStampedModel


class DailySummary(TimeStampedModel):
    """Pre-computed daily sales summary for fast dashboard loading."""
    restaurant = models.ForeignKey(
        'tenants.Restaurant', on_delete=models.CASCADE,
        related_name='daily_summaries'
    )
    date = models.DateField()

    # Order counts
    total_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)

    # Financials
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    service_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discounts_given = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Averages
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Breakdown data
    top_selling_items = models.JSONField(default=list, blank=True)
    payment_method_breakdown = models.JSONField(default=dict, blank=True)
    hourly_order_counts = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ['restaurant', 'date']
        ordering = ['-date']
        verbose_name_plural = 'Daily summaries'

    def __str__(self):
        return f"{self.restaurant.name} — {self.date}"
