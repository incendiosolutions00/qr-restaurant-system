from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrAbove, IsSuperAdmin
from apps.orders.models import Order, OrderItem
from apps.reports.models import DailySummary
from apps.reports.serializers import DailySummarySerializer


class DailySummaryListView(generics.ListAPIView):
    """Restaurant — view daily summaries."""
    serializer_class = DailySummarySerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        qs = DailySummary.objects.filter(
            restaurant=self.request.user.restaurant,
        )
        # Optional date range filter
        start = self.request.query_params.get('start_date')
        end = self.request.query_params.get('end_date')
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)
        return qs


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsManagerOrAbove])
def dashboard(request):
    """Restaurant — dashboard overview with live stats."""
    restaurant = request.user.restaurant
    today = timezone.localdate()

    todays_orders = Order.objects.filter(
        restaurant=restaurant,
        created_at__date=today,
    )

    completed_today = todays_orders.filter(status='completed')
    todays_revenue = completed_today.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')

    pending_orders = todays_orders.filter(
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).count()

    active_tables = restaurant.tables.filter(status='occupied').count()

    avg_order_value = completed_today.aggregate(
        avg=Avg('total')
    )['avg'] or Decimal('0.00')

    # Top selling items today
    top_items = (
        OrderItem.objects.filter(
            order__restaurant=restaurant,
            order__created_at__date=today,
        )
        .values('menu_item__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )

    return Response({
        'todays_orders': todays_orders.count(),
        'todays_revenue': str(todays_revenue),
        'pending_orders': pending_orders,
        'active_tables': active_tables,
        'total_tables': restaurant.tables.filter(is_active=True).count(),
        'avg_order_value': str(round(avg_order_value, 2)),
        'top_items_today': list(top_items),
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsManagerOrAbove])
def sales_report(request):
    """Restaurant — sales report for a date range."""
    restaurant = request.user.restaurant
    start_date = request.query_params.get('start_date', str(date.today() - timedelta(days=30)))
    end_date = request.query_params.get('end_date', str(date.today()))

    orders = Order.objects.filter(
        restaurant=restaurant,
        status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    stats = orders.aggregate(
        total_orders=Count('id'),
        gross_revenue=Sum('total'),
        tax_collected=Sum('tax_amount'),
        service_charges=Sum('service_charge'),
        discounts_given=Sum('discount_amount'),
        avg_order_value=Avg('total'),
    )

    # Clean None values
    for key in stats:
        if stats[key] is None:
            stats[key] = 0

    return Response({
        'start_date': start_date,
        'end_date': end_date,
        **stats,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsManagerOrAbove])
def item_sales_report(request):
    """Restaurant — which items are selling the most."""
    restaurant = request.user.restaurant
    start_date = request.query_params.get('start_date', str(date.today() - timedelta(days=30)))
    end_date = request.query_params.get('end_date', str(date.today()))

    items = (
        OrderItem.objects.filter(
            order__restaurant=restaurant,
            order__status='completed',
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        )
        .values('menu_item__id', 'menu_item__name', 'menu_item__price')
        .annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum('subtotal'),
        )
        .order_by('-total_qty')
    )

    return Response(list(items))


# ─── SUPER ADMIN — GLOBAL ANALYTICS ─────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsSuperAdmin])
def super_admin_analytics(request):
    """Super admin — platform-wide analytics."""
    from django.contrib.auth import get_user_model
    from apps.tenants.models import Restaurant
    from apps.subscriptions.models import Subscription

    User = get_user_model()
    today = timezone.localdate()

    total_restaurants = Restaurant.objects.count()
    active_restaurants = Restaurant.objects.filter(is_active=True, is_approved=True).count()
    total_orders_today = Order.objects.filter(created_at__date=today).count()
    total_revenue_today = Order.objects.filter(
        created_at__date=today, status='completed',
    ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')

    active_subscriptions = Subscription.objects.filter(
        status__in=['trial', 'active'],
    ).count()

    total_users = User.objects.count()

    return Response({
        'total_restaurants': total_restaurants,
        'active_restaurants': active_restaurants,
        'total_orders_today': total_orders_today,
        'total_revenue_today': str(total_revenue_today),
        'active_subscriptions': active_subscriptions,
        'total_users': total_users,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsSuperAdmin])
def super_admin_orders_revenue(request):
    """Super admin — detailed orders & revenue per restaurant with date filters."""
    from apps.tenants.models import Restaurant

    start_date = request.query_params.get('start_date', str(date.today()))
    end_date = request.query_params.get('end_date', str(date.today()))

    # Per-restaurant breakdown
    restaurants = Restaurant.objects.filter(
        is_active=True, is_approved=True,
    ).order_by('name')

    breakdown = []
    totals = {'total_orders': 0, 'completed_orders': 0, 'pending_orders': 0, 'revenue': Decimal('0.00')}

    for r in restaurants:
        orders = Order.objects.filter(
            restaurant=r,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        total = orders.count()
        completed = orders.filter(status='completed').count()
        pending = orders.filter(status__in=['pending', 'confirmed', 'preparing', 'ready']).count()
        revenue = orders.filter(status='completed').aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        if total > 0:
            breakdown.append({
                'restaurant_id': r.id,
                'restaurant_name': r.name,
                'restaurant_slug': r.slug,
                'total_orders': total,
                'completed_orders': completed,
                'pending_orders': pending,
                'cancelled_orders': orders.filter(status='cancelled').count(),
                'revenue': str(revenue),
            })

        totals['total_orders'] += total
        totals['completed_orders'] += completed
        totals['pending_orders'] += pending
        totals['revenue'] += revenue

    totals['revenue'] = str(totals['revenue'])

    return Response({
        'start_date': start_date,
        'end_date': end_date,
        'totals': totals,
        'restaurants': breakdown,
    })
