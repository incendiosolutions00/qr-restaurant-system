"""
Template-serving views for the frontend pages.
These are simple views that render HTML templates — all data is fetched
via JavaScript calling the DRF API endpoints.
"""
from django.shortcuts import render


# ─── Customer Pages ──────────────────────────────────────────────
def customer_menu(request, slug, table_id):
    return render(request, 'customer/menu.html', {
        'slug': slug,
        'table_id': table_id,
    })


def customer_order_online(request, slug):
    return render(request, 'customer/order_online.html', {'slug': slug})


def customer_order_status(request, slug, order_number):
    return render(request, 'customer/order_status.html', {
        'slug': slug,
        'order_number': order_number,
    })


# ─── Admin Pages ─────────────────────────────────────────────────
def admin_login(request):
    return render(request, 'admin/login.html')


def admin_register(request):
    return render(request, 'admin/register.html')


def admin_dashboard(request):
    return render(request, 'admin/dashboard.html')


def admin_orders(request):
    return render(request, 'admin/orders.html')


def admin_kitchen(request):
    return render(request, 'admin/kitchen.html')


def admin_menu(request):
    return render(request, 'admin/menu.html')


def admin_deals(request):
    return render(request, 'admin/deals.html')


def admin_tables(request):
    return render(request, 'admin/tables.html')


def admin_staff(request):
    return render(request, 'admin/staff.html')


def admin_reports(request):
    return render(request, 'admin/reports.html')


def admin_settings(request):
    return render(request, 'admin/settings.html')


# ─── Super Admin Pages ──────────────────────────────────────────
def superadmin_dashboard(request):
    return render(request, 'superadmin/dashboard.html')


def superadmin_restaurants(request):
    return render(request, 'superadmin/restaurants.html')


def superadmin_plans(request):
    return render(request, 'superadmin/plans.html')


def superadmin_users(request):
    return render(request, 'superadmin/users.html')


def superadmin_orders_revenue(request):
    return render(request, 'superadmin/orders_revenue.html')
