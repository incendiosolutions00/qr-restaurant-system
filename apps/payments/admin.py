from django.contrib import admin

from apps.payments.models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'method', 'amount', 'status', 'transaction_id', 'created_at']
    list_filter = ['method', 'status', 'created_at']
    search_fields = ['transaction_id', 'order__order_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['payment', 'amount', 'processed_by', 'created_at']
    readonly_fields = ['created_at']
