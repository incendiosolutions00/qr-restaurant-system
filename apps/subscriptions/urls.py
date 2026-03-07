from django.urls import path

from apps.subscriptions import views

app_name = 'subscriptions'

urlpatterns = [
    # Public
    path('plans/', views.PlanListView.as_view(), name='plan-list'),

    # Restaurant owner
    path('my-subscription/', views.MySubscriptionView.as_view(), name='my-subscription'),
    path('my-subscription/payments/', views.MySubscriptionPaymentsView.as_view(), name='my-subscription-payments'),

    # Super admin
    path('superadmin/plans/', views.SuperAdminPlanListCreateView.as_view(), name='superadmin-plan-list'),
    path('superadmin/plans/<int:pk>/', views.SuperAdminPlanDetailView.as_view(), name='superadmin-plan-detail'),
    path('superadmin/subscriptions/', views.SuperAdminSubscriptionListView.as_view(), name='superadmin-subscription-list'),
    path('superadmin/subscriptions/<int:pk>/', views.SuperAdminSubscriptionDetailView.as_view(), name='superadmin-subscription-detail'),
]
