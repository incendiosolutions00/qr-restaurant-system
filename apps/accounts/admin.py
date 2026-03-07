from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'restaurant', 'is_active']
    list_filter = ['role', 'is_active', 'restaurant']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Restaurant Info', {
            'fields': ('role', 'restaurant', 'phone', 'avatar'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Restaurant Info', {
            'fields': ('role', 'restaurant', 'phone'),
        }),
    )
