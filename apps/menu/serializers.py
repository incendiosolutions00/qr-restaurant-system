from rest_framework import serializers

from apps.menu.models import (
    Category, Deal, DealItem, MenuItem, MenuItemVariant,
    Modifier, ModifierGroup,
)


class ModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modifier
        fields = ['id', 'name', 'price', 'is_available']


class ModifierGroupSerializer(serializers.ModelSerializer):
    modifiers = ModifierSerializer(many=True, read_only=True)

    class Meta:
        model = ModifierGroup
        fields = [
            'id', 'restaurant', 'name', 'is_required',
            'min_selections', 'max_selections', 'modifiers',
        ]
        read_only_fields = ['id', 'restaurant']


class MenuItemVariantSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = MenuItemVariant
        fields = ['id', 'name', 'price_adjustment', 'total_price', 'is_available']


class MenuItemSerializer(serializers.ModelSerializer):
    variants = MenuItemVariantSerializer(many=True, read_only=True)
    modifier_groups = ModifierGroupSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id', 'restaurant', 'category', 'category_name', 'name',
            'description', 'price', 'image', 'is_available', 'prep_time',
            'display_order', 'variants', 'modifier_groups',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at']


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """Separate serializer for creating/updating — no nested data."""
    modifier_group_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ModifierGroup.objects.all(),
        source='modifier_groups', required=False,
    )

    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'name', 'description', 'price', 'image',
            'is_available', 'prep_time', 'display_order', 'modifier_group_ids',
        ]
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    items_count = serializers.IntegerField(source='items.count', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'restaurant', 'name', 'description', 'image',
            'display_order', 'is_active', 'items_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at']


class CategoryWithItemsSerializer(serializers.ModelSerializer):
    """Full menu category with all its items (for customer menu view)."""
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'image',
            'display_order', 'items',
        ]


class DealItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_price = serializers.DecimalField(
        source='menu_item.price', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = DealItem
        fields = ['id', 'menu_item', 'menu_item_name', 'menu_item_price', 'quantity']


class DealSerializer(serializers.ModelSerializer):
    items = DealItemSerializer(many=True, read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Deal
        fields = [
            'id', 'restaurant', 'name', 'description', 'image',
            'discount_type', 'discount_value', 'start_date', 'end_date',
            'is_active', 'is_valid', 'items', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at']
