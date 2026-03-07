from django.contrib import admin

from apps.menu.models import (
    Category, Deal, DealItem, MenuItem, MenuItemVariant,
    Modifier, ModifierGroup,
)


class MenuItemVariantInline(admin.TabularInline):
    model = MenuItemVariant
    extra = 0


class ModifierInline(admin.TabularInline):
    model = Modifier
    extra = 0


class DealItemInline(admin.TabularInline):
    model = DealItem
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'display_order', 'is_active']
    list_filter = ['is_active', 'restaurant']
    search_fields = ['name']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'restaurant', 'price', 'is_available', 'prep_time']
    list_filter = ['is_available', 'category', 'restaurant']
    search_fields = ['name', 'description']
    inlines = [MenuItemVariantInline]


@admin.register(ModifierGroup)
class ModifierGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'is_required', 'min_selections', 'max_selections']
    list_filter = ['is_required', 'restaurant']
    inlines = [ModifierInline]


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'discount_type', 'discount_value', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active', 'discount_type', 'restaurant']
    inlines = [DealItemInline]
