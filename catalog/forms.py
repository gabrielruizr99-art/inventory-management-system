from django import forms
from django.db.models import Q

from .models import Category, Product


class BootstrapModelForm(forms.ModelForm):
    """Aplica estilos y atributos accesibles comunes a formularios del catálogo."""

    autocomplete = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class
            field.widget.attrs["autocomplete"] = self.autocomplete.get(name, "off")


class CategoryForm(BootstrapModelForm):
    autocomplete = {"name": "organization-title"}

    class Meta:
        model = Category
        fields = ["name", "description"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        duplicate = Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("Ya existe una categoría con este nombre.")
        return name


class ProductForm(BootstrapModelForm):
    autocomplete = {
        "sku": "off",
        "barcode": "off",
        "name": "off",
    }

    class Meta:
        model = Product
        fields = [
            "sku",
            "barcode",
            "name",
            "description",
            "category",
            "unit_of_measure",
            "sale_price",
        ]
        widgets = {"sale_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = Category.objects.filter(is_active=True)
        if self.instance.pk and self.instance.category_id:
            categories = Category.objects.filter(
                Q(is_active=True) | Q(pk=self.instance.category_id)
            )
        self.fields["category"].queryset = categories.order_by("name")

    def clean_sku(self):
        sku = self.cleaned_data["sku"].strip().upper()
        duplicate = Product.objects.filter(sku__iexact=sku).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("Ya existe un producto con este SKU.")
        return sku

    def clean_barcode(self):
        barcode = self.cleaned_data["barcode"].strip()
        if barcode:
            duplicate = Product.objects.filter(barcode=barcode).exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise forms.ValidationError("Ya existe un producto con este código de barras.")
        return barcode
