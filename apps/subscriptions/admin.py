from django.contrib import admin

from apps.subscriptions.models import Plan, Subscription, SubscriptionPayment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'price', 'billing_cycle', 'max_tables',
        'max_menu_items', 'has_pos', 'is_active',
    ]
    list_filter = ['is_active', 'billing_cycle']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['restaurant', 'plan', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'plan']
    search_fields = ['restaurant__name']


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'amount', 'payment_date', 'status']
    list_filter = ['status', 'payment_method']
