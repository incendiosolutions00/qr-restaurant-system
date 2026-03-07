from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Only super admins (us — the platform owners)."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.role == 'super_admin' or request.user.is_superuser)
        )


class IsRestaurantOwner(BasePermission):
    """Restaurant owner — full control over their restaurant."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'restaurant_owner'
        )


class IsRestaurantMember(BasePermission):
    """Any staff member (owner, manager, staff, kitchen) of a restaurant."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_restaurant_member
        )


class IsManagerOrAbove(BasePermission):
    """Restaurant owner or manager."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ['restaurant_owner', 'manager']
        )


class IsKitchenStaff(BasePermission):
    """Kitchen staff — can view and update order status."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'kitchen'
        )


class IsStaffOrAbove(BasePermission):
    """Staff, manager, or owner."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ['restaurant_owner', 'manager', 'staff']
        )
