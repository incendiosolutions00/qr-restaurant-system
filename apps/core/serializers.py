from rest_framework import serializers

from apps.core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True, default='System')

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'restaurant', 'action',
            'model_name', 'object_id', 'changes', 'ip_address', 'created_at',
        ]
        read_only_fields = fields
