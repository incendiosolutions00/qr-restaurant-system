from django.contrib import admin

from apps.core.models import AuditLog, SystemSetting


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'model_name', 'object_id', 'user', 'restaurant', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['model_name', 'object_id', 'user__username']
    readonly_fields = ['user', 'restaurant', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'created_at']
    ordering = ['-created_at']


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'description']
    search_fields = ['key']
