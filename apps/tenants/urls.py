from django.urls import path

from apps.tenants import views

app_name = 'tenants'

urlpatterns = [
    # Restaurant owner
    path('restaurant/profile/', views.RestaurantProfileView.as_view(), name='restaurant-profile'),

    # Table management
    path('restaurant/tables/', views.TableListCreateView.as_view(), name='table-list'),
    path('restaurant/tables/<int:pk>/', views.TableDetailView.as_view(), name='table-detail'),
    path('restaurant/tables/<int:pk>/regenerate-qr/', views.regenerate_qr, name='regenerate-qr'),
    path('restaurant/tables/<int:pk>/reset/', views.reset_table, name='reset-table'),

    # Table sessions
    path('restaurant/sessions/', views.TableSessionListView.as_view(), name='session-list'),
    path('restaurant/sessions/<int:pk>/close/', views.close_session, name='close-session'),

    # Super admin
    path('superadmin/restaurants/', views.SuperAdminRestaurantListView.as_view(), name='superadmin-restaurants'),
    path('superadmin/restaurants/<int:pk>/', views.SuperAdminRestaurantDetailView.as_view(), name='superadmin-restaurant-detail'),
    path('superadmin/restaurants/<int:pk>/approve/', views.approve_restaurant, name='approve-restaurant'),
    path('superadmin/restaurants/<int:pk>/update-owner/', views.update_restaurant_owner, name='superadmin-update-owner'),
    path('superadmin/restaurants/create/', views.create_restaurant_with_owner, name='superadmin-create-restaurant'),

    # Public / Customer
    path('r/<slug:slug>/', views.CustomerRestaurantView.as_view(), name='customer-restaurant'),
    path('r/<slug:slug>/table/<int:table_id>/', views.customer_table_info, name='customer-table-info'),
]
