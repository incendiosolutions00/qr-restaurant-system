from rest_framework import generics, permissions

from apps.accounts.permissions import IsManagerOrAbove
from apps.core.models import AuditLog
from apps.core.serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    """Restaurant — view audit trail."""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]
    filterset_fields = ['action', 'model_name']

    def get_queryset(self):
        return AuditLog.objects.filter(
            restaurant=self.request.user.restaurant,
        ).select_related('user')
