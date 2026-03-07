from django.contrib import admin

from apps.tenants.models import Restaurant, Table, TableSession


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'owner', 'city', 'is_active', 'is_approved', 'created_at']
    list_filter = ['is_active', 'is_approved', 'city', 'country']
    search_fields = ['name', 'slug', 'email', 'city']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'restaurant', 'capacity', 'status', 'is_active']
    list_filter = ['status', 'is_active', 'restaurant']
    search_fields = ['restaurant__name']


@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'table', 'is_active', 'guest_count', 'started_at', 'ended_at']
    list_filter = ['is_active']
    readonly_fields = ['session_id', 'started_at']
