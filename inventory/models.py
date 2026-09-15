from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Trim, Upper


class Location(models.Model):
    class LocationType(models.TextChoices):
        BRANCH = "BRANCH", "Sucursal"
        WAREHOUSE = "WAREHOUSE", "Almacén"

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    location_type = models.CharField(max_length=20, choices=LocationType.choices)
    address = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "code"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(code__regex=r"^\s*$"),
                name="inventory_location_code_not_blank",
            ),
            models.UniqueConstraint(
                Upper(Trim("code")),
                name="inventory_location_code_ci_uniq",
            ),
            models.CheckConstraint(
                condition=~models.Q(name__regex=r"^\s*$"),
                name="inventory_location_name_not_blank",
            ),
            models.CheckConstraint(
                condition=models.Q(location_type__in=("BRANCH", "WAREHOUSE")),
                name="inventory_location_type_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["location_type", "is_active"],
                name="inv_location_type_active_idx",
            ),
        ]
        permissions = [
            ("change_location_status", "Can change location status"),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        self._normalize_fields()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self._normalize_fields()
        errors = {}
        if not self.code:
            errors["code"] = "El código de la ubicación es obligatorio."
        if not self.name:
            errors["name"] = "El nombre de la ubicación es obligatorio."
        if errors:
            raise ValidationError(errors)

    def _normalize_fields(self):
        self.code = self.code.strip().upper()
        self.name = self.name.strip()
        self.address = self.address.strip()
