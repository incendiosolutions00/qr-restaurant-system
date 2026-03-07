from django.urls import path

from apps.reports import views

app_name = 'reports'

urlpatterns = [
    # Restaurant
    path('restaurant/reports/dashboard/', views.dashboard, name='dashboard'),
    path('restaurant/reports/daily/', views.DailySummaryListView.as_view(), name='daily-summary'),
    path('restaurant/reports/sales/', views.sales_report, name='sales-report'),
    path('restaurant/reports/items/', views.item_sales_report, name='item-sales-report'),

    # Super admin
    path('superadmin/analytics/', views.super_admin_analytics, name='superadmin-analytics'),
    path('superadmin/analytics/orders/', views.super_admin_orders_revenue, name='superadmin-orders-revenue'),
]
