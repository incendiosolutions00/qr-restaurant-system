from django.urls import path

from apps.notifications import views

app_name = 'notifications'

urlpatterns = [
    # Staff
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='notification-read'),
    path('notifications/read-all/', views.mark_all_read, name='notifications-read-all'),

    # Waiter calls — staff
    path('restaurant/waiter-calls/', views.WaiterCallListView.as_view(), name='waiter-call-list'),
    path('restaurant/waiter-calls/<int:pk>/respond/', views.respond_to_waiter_call, name='waiter-call-respond'),

    # Waiter calls — customer (public)
    path('r/<slug:slug>/waiter-call/', views.CustomerWaiterCallView.as_view(), name='customer-waiter-call'),
]
