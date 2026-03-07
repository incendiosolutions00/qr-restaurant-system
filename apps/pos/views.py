from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsStaffOrAbove
from apps.pos.models import POSSession, CashDrawerLog
from apps.pos.serializers import POSSessionSerializer, CashDrawerLogSerializer
from apps.tenants.models import Table
from apps.tenants.serializers import TableSerializer


class POSSessionListCreateView(generics.ListCreateAPIView):
    """List POS sessions or open a new one."""
    serializer_class = POSSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAbove]

    def get_queryset(self):
        return POSSession.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(
            restaurant=self.request.user.restaurant,
            staff=self.request.user,
        )


class POSSessionDetailView(generics.RetrieveAPIView):
    """View a POS session."""
    serializer_class = POSSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAbove]

    def get_queryset(self):
        return POSSession.objects.filter(restaurant=self.request.user.restaurant)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsStaffOrAbove])
def close_pos_session(request, pk):
    """Close a POS session with closing cash count."""
    try:
        session = POSSession.objects.get(
            pk=pk,
            restaurant=request.user.restaurant,
            is_active=True,
        )
    except POSSession.DoesNotExist:
        return Response(
            {'detail': 'Active POS session not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    closing_cash = request.data.get('closing_cash')
    notes = request.data.get('notes', '')

    session.close_session(
        closing_cash=closing_cash if closing_cash is not None else None,
    )
    if notes:
        session.notes = notes
        session.save(update_fields=['notes'])

    return Response(POSSessionSerializer(session).data)


class CashDrawerLogListCreateView(generics.ListCreateAPIView):
    """View or add cash drawer logs for a POS session."""
    serializer_class = CashDrawerLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrAbove]

    def get_queryset(self):
        return CashDrawerLog.objects.filter(
            pos_session_id=self.kwargs['session_pk'],
            pos_session__restaurant=self.request.user.restaurant,
        )

    def perform_create(self, serializer):
        serializer.save(pos_session_id=self.kwargs['session_pk'])


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsStaffOrAbove])
def table_overview(request):
    """POS — overview of all tables with their current status."""
    tables = Table.objects.filter(
        restaurant=request.user.restaurant,
        is_active=True,
    ).order_by('number')

    return Response(TableSerializer(tables, many=True, context={'request': request}).data)
