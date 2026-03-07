from django.urls import path

from apps.orders import views

app_name = 'orders'

urlpatterns = [
    # Customer (Public)
    path('r/<slug:slug>/orders/', views.CustomerPlaceOrderView.as_view(), name='customer-place-order'),
    path('r/<slug:slug>/orders/<str:order_number>/status/', views.CustomerOrderStatusView.as_view(), name='customer-order-status'),

    # Restaurant staff
    path('restaurant/orders/', views.OrderListView.as_view(), name='order-list'),
    path('restaurant/orders/active/', views.ActiveOrdersView.as_view(), name='active-orders'),
    path('restaurant/orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('restaurant/orders/<int:pk>/status/', views.update_order_status, name='update-order-status'),

    # Kitchen
    path('kitchen/orders/', views.KitchenOrdersView.as_view(), name='kitchen-orders'),
]
