from rest_framework import serializers

from apps.notifications.models import Notification, WaiterCall


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'restaurant', 'recipient', 'target_role',
            'notification_type', 'title', 'message', 'data',
            'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'restaurant', 'created_at']


class WaiterCallSerializer(serializers.ModelSerializer):
    table_number = serializers.IntegerField(source='table.number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WaiterCall
        fields = [
            'id', 'restaurant', 'table', 'table_number', 'table_session',
            'status', 'status_display', 'note',
            'responded_by', 'responded_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'restaurant', 'responded_by', 'responded_at', 'created_at',
        ]


class WaiterCallCreateSerializer(serializers.Serializer):
    """Customer calling a waiter from their table."""
    table_id = serializers.IntegerField()
    session_id = serializers.UUIDField(required=False)
    note = serializers.CharField(required=False, default='')
