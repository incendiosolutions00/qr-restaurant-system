from django.db.models import ProtectedError
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from apps.accounts.permissions import IsRestaurantOwner, IsSuperAdmin
from apps.subscriptions.models import Plan, Subscription, SubscriptionPayment
from apps.subscriptions.serializers import (
    PlanSerializer, SubscriptionPaymentSerializer, SubscriptionSerializer,
)


# ─── PUBLIC — VIEW PLANS ────────────────────────────────────────────────────

class PlanListView(generics.ListAPIView):
    """Public — list all active subscription plans."""
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Plan.objects.filter(is_active=True)


# ─── SUPER ADMIN — PLAN MANAGEMENT ──────────────────────────────────────────

class SuperAdminPlanListCreateView(generics.ListCreateAPIView):
    """Super admin — manage subscription plans."""
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    queryset = Plan.objects.all()


class SuperAdminPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Super admin — view, update or delete a plan."""
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    queryset = Plan.objects.all()

    def destroy(self, request, *args, **kwargs):
        plan = self.get_object()
        # Check how many restaurants are using this plan
        active_subs = Subscription.objects.filter(plan=plan).select_related('restaurant')
        if active_subs.exists():
            restaurant_names = ', '.join(
                sub.restaurant.name for sub in active_subs[:5]
            )
            count = active_subs.count()
            extra = f' and {count - 5} more' if count > 5 else ''
            return Response(
                {'detail': f'Cannot delete this plan because {count} restaurant(s) are using it: '
                           f'{restaurant_names}{extra}. '
                           f'Please change their plan first or deactivate this plan instead.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': 'Cannot delete this plan because it is linked to existing subscriptions. '
                           'Please deactivate it instead.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ─── SUPER ADMIN — SUBSCRIPTION MANAGEMENT ──────────────────────────────────

class SuperAdminSubscriptionListView(generics.ListCreateAPIView):
    """Super admin — manage restaurant subscriptions."""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    queryset = Subscription.objects.all().select_related('restaurant', 'plan')
    filterset_fields = ['status', 'plan']


class SuperAdminSubscriptionDetailView(generics.RetrieveUpdateAPIView):
    """Super admin — view or update a subscription."""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    queryset = Subscription.objects.all()


# ─── RESTAURANT OWNER — VIEW SUBSCRIPTION ───────────────────────────────────

class MySubscriptionView(generics.RetrieveAPIView):
    """Restaurant owner — view their subscription details."""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]

    def get_object(self):
        return Subscription.objects.get(restaurant__owner=self.request.user)


class MySubscriptionPaymentsView(generics.ListAPIView):
    """Restaurant owner — view subscription payment history."""
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]

    def get_queryset(self):
        return SubscriptionPayment.objects.filter(
            subscription__restaurant__owner=self.request.user,
        )
