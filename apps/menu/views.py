from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrAbove
from apps.menu.models import (
    Category, Deal, DealItem, MenuItem, MenuItemVariant,
    Modifier, ModifierGroup,
)
from apps.menu.serializers import (
    CategorySerializer, CategoryWithItemsSerializer, DealItemSerializer,
    DealSerializer, MenuItemCreateSerializer, MenuItemSerializer,
    MenuItemVariantSerializer, ModifierGroupSerializer, ModifierSerializer,
)


# ─── CATEGORIES ──────────────────────────────────────────────────────────────

class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return Category.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return Category.objects.filter(restaurant=self.request.user.restaurant)


# ─── MENU ITEMS ──────────────────────────────────────────────────────────────

class MenuItemListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MenuItemCreateSerializer
        return MenuItemSerializer

    def get_queryset(self):
        return MenuItem.objects.filter(
            restaurant=self.request.user.restaurant
        ).select_related('category').prefetch_related('variants', 'modifier_groups__modifiers')

    def perform_create(self, serializer):
        from apps.core.utils import check_plan_limit
        check_plan_limit(self.request.user.restaurant, 'menu_items')
        serializer.save(restaurant=self.request.user.restaurant)


class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MenuItemCreateSerializer
        return MenuItemSerializer

    def get_queryset(self):
        return MenuItem.objects.filter(restaurant=self.request.user.restaurant)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated, IsManagerOrAbove])
def toggle_item_availability(request, pk):
    """Quick toggle for sold out / available."""
    try:
        item = MenuItem.objects.get(pk=pk, restaurant=request.user.restaurant)
    except MenuItem.DoesNotExist:
        return Response({'detail': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)
    item.is_available = not item.is_available
    item.save(update_fields=['is_available', 'updated_at'])
    return Response({
        'id': item.id,
        'name': item.name,
        'is_available': item.is_available,
    })


# ─── VARIANTS ────────────────────────────────────────────────────────────────

class VariantListCreateView(generics.ListCreateAPIView):
    serializer_class = MenuItemVariantSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return MenuItemVariant.objects.filter(
            menu_item__restaurant=self.request.user.restaurant,
            menu_item_id=self.kwargs['item_pk'],
        )

    def perform_create(self, serializer):
        item = MenuItem.objects.get(
            pk=self.kwargs['item_pk'],
            restaurant=self.request.user.restaurant,
        )
        serializer.save(menu_item=item)


class VariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MenuItemVariantSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return MenuItemVariant.objects.filter(
            menu_item__restaurant=self.request.user.restaurant,
        )


# ─── MODIFIER GROUPS & MODIFIERS ────────────────────────────────────────────

class ModifierGroupListCreateView(generics.ListCreateAPIView):
    serializer_class = ModifierGroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return ModifierGroup.objects.filter(
            restaurant=self.request.user.restaurant
        ).prefetch_related('modifiers')

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.restaurant)


class ModifierGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ModifierGroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return ModifierGroup.objects.filter(restaurant=self.request.user.restaurant)


class ModifierListCreateView(generics.ListCreateAPIView):
    serializer_class = ModifierSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return Modifier.objects.filter(
            group__restaurant=self.request.user.restaurant,
            group_id=self.kwargs['group_pk'],
        )

    def perform_create(self, serializer):
        group = ModifierGroup.objects.get(
            pk=self.kwargs['group_pk'],
            restaurant=self.request.user.restaurant,
        )
        serializer.save(group=group)


class ModifierDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ModifierSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return Modifier.objects.filter(
            group__restaurant=self.request.user.restaurant,
        )


# ─── DEALS ───────────────────────────────────────────────────────────────────

class DealListCreateView(generics.ListCreateAPIView):
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return Deal.objects.filter(
            restaurant=self.request.user.restaurant
        ).prefetch_related('items__menu_item')

    def perform_create(self, serializer):
        from apps.core.utils import check_plan_limit
        check_plan_limit(self.request.user.restaurant, 'deals')
        serializer.save(restaurant=self.request.user.restaurant)


class DealDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return Deal.objects.filter(restaurant=self.request.user.restaurant)


class DealItemListCreateView(generics.ListCreateAPIView):
    serializer_class = DealItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return DealItem.objects.filter(
            deal__restaurant=self.request.user.restaurant,
            deal_id=self.kwargs['deal_pk'],
        )

    def perform_create(self, serializer):
        deal = Deal.objects.get(
            pk=self.kwargs['deal_pk'],
            restaurant=self.request.user.restaurant,
        )
        serializer.save(deal=deal)


# ─── PUBLIC / CUSTOMER MENU ─────────────────────────────────────────────────

class CustomerMenuView(generics.ListAPIView):
    """Public — full menu for a restaurant (categories + items)."""
    serializer_class = CategoryWithItemsSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        slug = self.kwargs['slug']
        return Category.objects.filter(
            restaurant__slug=slug,
            restaurant__is_active=True,
            restaurant__is_approved=True,
            is_active=True,
        ).prefetch_related(
            'items__variants',
            'items__modifier_groups__modifiers',
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Filter out unavailable items in the serialized response
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CustomerDealsView(generics.ListAPIView):
    """Public — active deals for a restaurant."""
    serializer_class = DealSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        from django.utils import timezone
        slug = self.kwargs['slug']
        now = timezone.now()
        return Deal.objects.filter(
            restaurant__slug=slug,
            restaurant__is_active=True,
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
        ).prefetch_related('items__menu_item')
