from django.contrib import admin

from apps.notifications.models import Notification, WaiterCall


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'restaurant', 'recipient', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'restaurant']
    search_fields = ['title', 'message']


@admin.register(WaiterCall)
class WaiterCallAdmin(admin.ModelAdmin):
    list_display = ['table', 'restaurant', 'status', 'responded_by', 'created_at', 'responded_at']
    list_filter = ['status', 'restaurant']
