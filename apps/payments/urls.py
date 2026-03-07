from django.urls import path

from apps.payments import views

app_name = 'payments'

urlpatterns = [
    path('restaurant/payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('restaurant/payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('restaurant/payments/cash/', views.process_cash_payment, name='cash-payment'),
    path('restaurant/payments/card/', views.process_card_payment, name='card-payment'),
    path('restaurant/payments/refund/', views.RefundCreateView.as_view(), name='refund-create'),
]
