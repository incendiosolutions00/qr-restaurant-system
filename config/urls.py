from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.core.template_views import (
    admin_dashboard, admin_deals, admin_kitchen, admin_login, admin_menu,
    admin_orders, admin_register, admin_reports, admin_settings, admin_staff,
    admin_tables, customer_menu, customer_order_status, superadmin_dashboard,
    superadmin_orders_revenue, superadmin_plans, superadmin_restaurants,
    superadmin_users,
)

urlpatterns = [
    # Root redirect
    path('', RedirectView.as_view(url='/admin-panel/login/', permanent=False)),

    # Django Admin
    path('admin/', admin.site.urls),

    # ─── Frontend Template Pages ─────────────────────────────────
    # Customer pages
    path('r/<slug:slug>/table/<int:table_id>/menu/', customer_menu, name='customer-menu-page'),
    path('r/<slug:slug>/order/<str:order_number>/', customer_order_status, name='customer-order-page'),

    # Admin panel pages
    path('admin-panel/login/', admin_login, name='admin-login-page'),
    path('admin-panel/register/', admin_register, name='admin-register-page'),
    path('admin-panel/', admin_dashboard, name='admin-dashboard-page'),
    path('admin-panel/orders/', admin_orders, name='admin-orders-page'),
    path('admin-panel/kitchen/', admin_kitchen, name='admin-kitchen-page'),
    path('admin-panel/menu/', admin_menu, name='admin-menu-page'),
    path('admin-panel/deals/', admin_deals, name='admin-deals-page'),
    path('admin-panel/tables/', admin_tables, name='admin-tables-page'),
    path('admin-panel/staff/', admin_staff, name='admin-staff-page'),
    path('admin-panel/reports/', admin_reports, name='admin-reports-page'),
    path('admin-panel/settings/', admin_settings, name='admin-settings-page'),

    # Super admin pages
    path('superadmin/', superadmin_dashboard, name='superadmin-dashboard-page'),
    path('superadmin/restaurants/', superadmin_restaurants, name='superadmin-restaurants-page'),
    path('superadmin/plans/', superadmin_plans, name='superadmin-plans-page'),
    path('superadmin/users/', superadmin_users, name='superadmin-users-page'),
    path('superadmin/orders-revenue/', superadmin_orders_revenue, name='superadmin-orders-revenue-page'),

    # ─── API Endpoints ───────────────────────────────────────────
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.tenants.urls')),
    path('api/', include('apps.menu.urls')),
    path('api/', include('apps.orders.urls')),
    path('api/', include('apps.payments.urls')),
    path('api/', include('apps.pos.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.subscriptions.urls')),
    path('api/', include('apps.reports.urls')),
    path('api/', include('apps.core.urls')),
]

# Serve media & static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
