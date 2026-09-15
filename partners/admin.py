from django.contrib import admin

from .models import Customer, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "tax_id", "contact_name", "email", "is_active")
    search_fields = ("name", "tax_id", "contact_name", "email", "phone")
    list_filter = ("is_active",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "document_number", "email", "phone", "is_active")
    search_fields = ("name", "document_number", "email", "phone")
    list_filter = ("is_active",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
