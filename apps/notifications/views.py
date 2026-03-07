from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsRestaurantMember
from apps.notifications.models import Notification, WaiterCall
from apps.notifications.serializers import (
    NotificationSerializer, WaiterCallCreateSerializer, WaiterCallSerializer,
)
from apps.tenants.models import Restaurant, Table, TableSession


class NotificationListView(generics.ListAPIView):
    """Staff — list notifications for the current user."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantMember]

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(
            restaurant=user.restaurant,
        ).filter(
            Q(recipient=user) | Q(target_role=user.role)
        )


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated, IsRestaurantMember])
def mark_notification_read(request, pk):
    """Mark a notification as read."""
    try:
        notification = Notification.objects.get(
            pk=pk, restaurant=request.user.restaurant,
        )
    except Notification.DoesNotExist:
        return Response(
            {'detail': 'Notification not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    notification.is_read = True
    notification.save(update_fields=['is_read', 'updated_at'])
    return Response({'detail': 'Marked as read.'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsRestaurantMember])
def mark_all_read(request):
    """Mark all notifications as read for the current user."""
    Notification.objects.filter(
        restaurant=request.user.restaurant,
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)
    return Response({'detail': 'All notifications marked as read.'})


# ─── WAITER CALLS ───────────────────────────────────────────────────────────

class CustomerWaiterCallView(generics.CreateAPIView):
    """Public — customer calls a waiter from their table."""
    serializer_class = WaiterCallCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, slug, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            restaurant = Restaurant.objects.get(slug=slug, is_active=True)
            table = Table.objects.get(pk=data['table_id'], restaurant=restaurant)
        except (Restaurant.DoesNotExist, Table.DoesNotExist):
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check for existing pending call
        existing = WaiterCall.objects.filter(
            table=table, status=WaiterCall.Status.PENDING
        ).first()
        if existing:
            return Response(
                {'detail': 'Waiter has already been called for this table.'},
                status=status.HTTP_409_CONFLICT,
            )

        session = None
        if data.get('session_id'):
            session = TableSession.objects.filter(
                session_id=data['session_id'], is_active=True
            ).first()

        call = WaiterCall.objects.create(
            restaurant=restaurant,
            table=table,
            table_session=session,
            note=data.get('note', ''),
        )

        return Response(
            WaiterCallSerializer(call).data,
            status=status.HTTP_201_CREATED,
        )


class WaiterCallListView(generics.ListAPIView):
    """Staff — list waiter calls for the restaurant."""
    serializer_class = WaiterCallSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantMember]
    filterset_fields = ['status']

    def get_queryset(self):
        return WaiterCall.objects.filter(
            restaurant=self.request.user.restaurant,
        ).select_related('table')


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated, IsRestaurantMember])
def respond_to_waiter_call(request, pk):
    """Staff — acknowledge or resolve a waiter call."""
    try:
        call = WaiterCall.objects.get(
            pk=pk, restaurant=request.user.restaurant,
        )
    except WaiterCall.DoesNotExist:
        return Response(
            {'detail': 'Waiter call not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    new_status = request.data.get('status')
    if new_status not in ['acknowledged', 'resolved']:
        return Response(
            {'detail': 'Status must be "acknowledged" or "resolved".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    call.status = new_status
    call.responded_by = request.user
    call.responded_at = timezone.now()
    call.save(update_fields=['status', 'responded_by', 'responded_at', 'updated_at'])

    return Response(WaiterCallSerializer(call).data)
