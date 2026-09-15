from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower, Trim, Upper


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(name__regex=r"^\s*$"),
                name="catalog_category_name_not_blank",
            ),
            models.UniqueConstraint(
                Lower(Trim("name")),
                name="catalog_category_name_ci_uniq",
            ),
        ]
        permissions = [
            ("change_category_status", "Can change category status"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self._normalize_fields()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self._normalize_fields()
        if not self.name:
            raise ValidationError({"name": "El nombre de la categoría es obligatorio."})

    def _normalize_fields(self):
        self.name = self.name.strip()
        self.description = self.description.strip()


class Product(models.Model):
    class UnitOfMeasure(models.TextChoices):
        UNIT = "UNIT", "Unidad"
        KILOGRAM = "KILOGRAM", "Kilogramo"
        GRAM = "GRAM", "Gramo"
        LITER = "LITER", "Litro"
        MILLILITER = "MILLILITER", "Mililitro"
        METER = "METER", "Metro"
        CENTIMETER = "CENTIMETER", "Centímetro"
        BOX = "BOX", "Caja"
        PACKAGE = "PACKAGE", "Paquete"

    sku = models.CharField(max_length=50)
    barcode = models.CharField(max_length=64, blank=True, default="")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    unit_of_measure = models.CharField(
        max_length=20,
        choices=UnitOfMeasure.choices,
        default=UnitOfMeasure.UNIT,
    )
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "sku"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(sku__regex=r"^\s*$"),
                name="catalog_product_sku_not_blank",
            ),
            models.UniqueConstraint(
                Upper(Trim("sku")),
                name="catalog_product_sku_ci_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(barcode="") | ~models.Q(barcode__regex=r"^\s*$"),
                name="catalog_product_barcode_valid",
            ),
            models.UniqueConstraint(
                Trim("barcode"),
                condition=~models.Q(barcode=""),
                name="catalog_product_barcode_uniq",
            ),
            models.CheckConstraint(
                condition=~models.Q(name__regex=r"^\s*$"),
                name="catalog_product_name_not_blank",
            ),
            models.CheckConstraint(
                condition=models.Q(sale_price__gte=Decimal("0")),
                name="catalog_product_sale_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    unit_of_measure__in=(
                        "UNIT",
                        "KILOGRAM",
                        "GRAM",
                        "LITER",
                        "MILLILITER",
                        "METER",
                        "CENTIMETER",
                        "BOX",
                        "PACKAGE",
                    )
                ),
                name="catalog_product_unit_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["category", "is_active"],
                name="cat_product_cat_active_idx",
            ),
        ]
        permissions = [
            ("change_product_status", "Can change product status"),
        ]

    def __str__(self):
        return f"{self.sku} — {self.name}"

    def save(self, *args, **kwargs):
        self._normalize_fields()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self._normalize_fields()
        errors = {}
        if not self.sku:
            errors["sku"] = "El SKU es obligatorio."
        if not self.name:
            errors["name"] = "El nombre del producto es obligatorio."
        if self.sale_price is not None and self.sale_price < Decimal("0"):
            errors["sale_price"] = "El precio de venta no puede ser negativo."
        if errors:
            raise ValidationError(errors)

    def _normalize_fields(self):
        self.sku = self.sku.strip().upper()
        self.barcode = self.barcode.strip()
        self.name = self.name.strip()
        self.description = self.description.strip()
