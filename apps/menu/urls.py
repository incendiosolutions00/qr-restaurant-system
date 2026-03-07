from django.urls import path

from apps.menu import views

app_name = 'menu'

urlpatterns = [
    # Admin — Categories
    path('restaurant/menu/categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('restaurant/menu/categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),

    # Admin — Menu Items
    path('restaurant/menu/items/', views.MenuItemListCreateView.as_view(), name='menuitem-list'),
    path('restaurant/menu/items/<int:pk>/', views.MenuItemDetailView.as_view(), name='menuitem-detail'),
    path('restaurant/menu/items/<int:pk>/toggle/', views.toggle_item_availability, name='menuitem-toggle'),

    # Admin — Variants
    path('restaurant/menu/items/<int:item_pk>/variants/', views.VariantListCreateView.as_view(), name='variant-list'),
    path('restaurant/menu/variants/<int:pk>/', views.VariantDetailView.as_view(), name='variant-detail'),

    # Admin — Modifier Groups
    path('restaurant/menu/modifier-groups/', views.ModifierGroupListCreateView.as_view(), name='modifiergroup-list'),
    path('restaurant/menu/modifier-groups/<int:pk>/', views.ModifierGroupDetailView.as_view(), name='modifiergroup-detail'),

    # Admin — Modifiers
    path('restaurant/menu/modifier-groups/<int:group_pk>/modifiers/', views.ModifierListCreateView.as_view(), name='modifier-list'),
    path('restaurant/menu/modifiers/<int:pk>/', views.ModifierDetailView.as_view(), name='modifier-detail'),

    # Admin — Deals
    path('restaurant/menu/deals/', views.DealListCreateView.as_view(), name='deal-list'),
    path('restaurant/menu/deals/<int:pk>/', views.DealDetailView.as_view(), name='deal-detail'),
    path('restaurant/menu/deals/<int:deal_pk>/items/', views.DealItemListCreateView.as_view(), name='deal-items'),

    # Public / Customer
    path('r/<slug:slug>/menu/', views.CustomerMenuView.as_view(), name='customer-menu'),
    path('r/<slug:slug>/deals/', views.CustomerDealsView.as_view(), name='customer-deals'),
]
