from rest_framework.exceptions import PermissionDenied

from apps.core.models import AuditLog


def get_plan(restaurant):
    """Return the active plan for a restaurant, or None."""
    try:
        sub = restaurant.subscription
        if sub.is_valid:
            return sub.plan
    except Exception:
        pass
    return None


def check_plan_limit(restaurant, resource_type):
    """
    Check if the restaurant has reached its plan limit for the given resource.
    Raises PermissionDenied if limit exceeded. Does nothing if no plan assigned.
    resource_type: 'tables', 'menu_items', 'staff', 'deals'
    """
    plan = get_plan(restaurant)
    if plan is None:
        return  # No plan = no restrictions

    from apps.tenants.models import Table
    from apps.menu.models import MenuItem, Deal
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if resource_type == 'tables':
        current = Table.objects.filter(restaurant=restaurant).count()
        if current >= plan.max_tables:
            raise PermissionDenied(
                f'Plan limit reached: Your "{plan.name}" plan allows max {plan.max_tables} tables. '
                f'You have {current}. Please upgrade your plan.'
            )
    elif resource_type == 'menu_items':
        current = MenuItem.objects.filter(restaurant=restaurant).count()
        if current >= plan.max_menu_items:
            raise PermissionDenied(
                f'Plan limit reached: Your "{plan.name}" plan allows max {plan.max_menu_items} menu items. '
                f'You have {current}. Please upgrade your plan.'
            )
    elif resource_type == 'staff':
        current = User.objects.filter(
            restaurant=restaurant, role__in=['manager', 'staff', 'kitchen']
        ).count()
        if current >= plan.max_staff_accounts:
            raise PermissionDenied(
                f'Plan limit reached: Your "{plan.name}" plan allows max {plan.max_staff_accounts} staff accounts. '
                f'You have {current}. Please upgrade your plan.'
            )
    elif resource_type == 'deals':
        if not plan.has_deals:
            raise PermissionDenied(
                f'Feature not available: Your "{plan.name}" plan does not include Deals. '
                f'Please upgrade your plan.'
            )


def check_plan_feature(restaurant, feature):
    """
    Check if a specific feature is enabled in the restaurant's plan.
    feature: 'pos', 'kitchen_display', 'reports', 'deals', 'online_payment'
    """
    plan = get_plan(restaurant)
    if plan is None:
        return  # No plan = no restrictions

    feature_map = {
        'pos': plan.has_pos,
        'kitchen_display': plan.has_kitchen_display,
        'reports': plan.has_reports,
        'deals': plan.has_deals,
        'online_payment': plan.has_online_payment,
    }
    if not feature_map.get(feature, True):
        raise PermissionDenied(
            f'Feature not available: Your "{plan.name}" plan does not include this feature. '
            f'Please upgrade your plan.'
        )


def create_audit_log(user, action, model_name, object_id, changes=None, restaurant=None, ip_address=None):
    """Helper to create audit log entries."""
    AuditLog.objects.create(
        user=user,
        restaurant=restaurant or getattr(user, 'restaurant', None),
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        changes=changes or {},
        ip_address=ip_address,
    )


def get_client_ip(request):
    """Extract client IP from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
