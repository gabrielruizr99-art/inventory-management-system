from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "category",
        "unit_of_measure",
        "sale_price",
        "is_active",
    )
    search_fields = ("sku", "barcode", "name")
    list_filter = ("category", "unit_of_measure", "is_active")
    ordering = ("name", "sku")
    readonly_fields = ("created_at", "updated_at")
