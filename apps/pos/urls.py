from django.urls import path

from apps.pos import views

app_name = 'pos'

urlpatterns = [
    path('pos/sessions/', views.POSSessionListCreateView.as_view(), name='pos-session-list'),
    path('pos/sessions/<int:pk>/', views.POSSessionDetailView.as_view(), name='pos-session-detail'),
    path('pos/sessions/<int:pk>/close/', views.close_pos_session, name='pos-session-close'),
    path('pos/sessions/<int:session_pk>/cash-logs/', views.CashDrawerLogListCreateView.as_view(), name='cash-log-list'),
    path('pos/tables/', views.table_overview, name='pos-table-overview'),
]
