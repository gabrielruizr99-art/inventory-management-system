from django.contrib import admin

from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "location_type", "is_active", "updated_at")
    search_fields = ("code", "name", "address")
    list_filter = ("location_type", "is_active")
    ordering = ("name", "code")
    readonly_fields = ("created_at", "updated_at")
