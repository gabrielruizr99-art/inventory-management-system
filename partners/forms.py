from django import forms

from .models import Customer, Supplier


class BootstrapModelForm(forms.ModelForm):
    """Aplica estilos y autocompletado apropiado a formularios de socios."""

    autocomplete = {
        "name": "organization",
        "contact_name": "name",
        "email": "email",
        "phone": "tel",
        "address": "street-address",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            field.widget.attrs["autocomplete"] = self.autocomplete.get(name, "off")


class SupplierForm(BootstrapModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "tax_id", "contact_name", "email", "phone", "address", "notes"]

    def clean_tax_id(self):
        tax_id = self.cleaned_data["tax_id"].strip().upper()
        if tax_id:
            duplicate = Supplier.objects.filter(tax_id__iexact=tax_id).exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise forms.ValidationError("Ya existe un proveedor con este identificador fiscal.")
        return tax_id


class CustomerForm(BootstrapModelForm):
    class Meta:
        model = Customer
        fields = ["name", "document_number", "email", "phone", "address", "notes"]

    def clean_document_number(self):
        document = self.cleaned_data["document_number"].strip().upper()
        if document:
            duplicate = Customer.objects.filter(document_number__iexact=document).exclude(
                pk=self.instance.pk
            )
            if duplicate.exists():
                raise forms.ValidationError("Ya existe un cliente con este documento.")
        return document
