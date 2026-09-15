from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Trim, Upper


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=30, blank=True, default="")
    contact_name = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(name__regex=r"^\s*$"),
                name="partners_supplier_name_not_blank",
            ),
            models.CheckConstraint(
                condition=models.Q(tax_id="") | ~models.Q(tax_id__regex=r"^\s*$"),
                name="partners_supplier_tax_id_valid",
            ),
            models.UniqueConstraint(
                Upper(Trim("tax_id")),
                condition=~models.Q(tax_id=""),
                name="partners_supplier_tax_id_ci_uniq",
            ),
        ]
        permissions = [
            ("change_supplier_status", "Can change supplier status"),
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
            raise ValidationError({"name": "El nombre del proveedor es obligatorio."})

    def _normalize_fields(self):
        self.name = self.name.strip()
        self.tax_id = self.tax_id.strip().upper()
        self.contact_name = self.contact_name.strip()
        self.email = self.email.strip()
        self.phone = self.phone.strip()
        self.address = self.address.strip()
        self.notes = self.notes.strip()


class Customer(models.Model):
    name = models.CharField(max_length=200)
    document_number = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    address = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(name__regex=r"^\s*$"),
                name="partners_customer_name_not_blank",
            ),
            models.CheckConstraint(
                condition=models.Q(document_number="") | ~models.Q(document_number__regex=r"^\s*$"),
                name="partners_customer_document_valid",
            ),
            models.UniqueConstraint(
                Upper(Trim("document_number")),
                condition=~models.Q(document_number=""),
                name="partners_customer_document_ci_uniq",
            ),
        ]
        permissions = [
            ("change_customer_status", "Can change customer status"),
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
            raise ValidationError({"name": "El nombre del cliente es obligatorio."})

    def _normalize_fields(self):
        self.name = self.name.strip()
        self.document_number = self.document_number.strip().upper()
        self.email = self.email.strip()
        self.phone = self.phone.strip()
        self.address = self.address.strip()
        self.notes = self.notes.strip()
