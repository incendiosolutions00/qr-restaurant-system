from django.contrib import admin

from apps.reports.models import DailySummary


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = [
        'restaurant', 'date', 'total_orders', 'completed_orders',
        'gross_revenue', 'net_revenue',
    ]
    list_filter = ['restaurant', 'date']
    readonly_fields = [
        'restaurant', 'date', 'total_orders', 'completed_orders',
        'cancelled_orders', 'gross_revenue', 'tax_collected',
        'service_charges', 'discounts_given', 'net_revenue',
        'avg_order_value', 'top_selling_items',
        'payment_method_breakdown', 'hourly_order_counts',
    ]
