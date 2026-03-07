from django.contrib import admin

from apps.pos.models import POSSession, CashDrawerLog


class CashDrawerLogInline(admin.TabularInline):
    model = CashDrawerLog
    extra = 0


@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    list_display = ['staff', 'restaurant', 'opened_at', 'closed_at', 'is_active', 'opening_cash', 'closing_cash']
    list_filter = ['is_active', 'restaurant']
    inlines = [CashDrawerLogInline]
