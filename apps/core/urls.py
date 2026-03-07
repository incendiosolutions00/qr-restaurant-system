from django.urls import path

from apps.core import views

app_name = 'core'

urlpatterns = [
    path('restaurant/audit-logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
]
