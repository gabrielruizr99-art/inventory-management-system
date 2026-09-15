import pytest

from partners.forms import CustomerForm, SupplierForm
from partners.models import Customer, Supplier

SUPPLIER_FIELDS = ["name", "tax_id", "contact_name", "email", "phone", "address", "notes"]
CUSTOMER_FIELDS = ["name", "document_number", "email", "phone", "address", "notes"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("form_class", "fields", "data", "model"),
    [
        (
            SupplierForm,
            SUPPLIER_FIELDS,
            {
                "name": "Proveedor",
                "tax_id": "RUC-1",
                "contact_name": "Contacto",
                "email": "proveedor@example.test",
                "phone": "555-0100",
                "address": "Dirección",
                "notes": "Nota",
                "is_active": False,
            },
            Supplier,
        ),
        (
            CustomerForm,
            CUSTOMER_FIELDS,
            {
                "name": "Cliente",
                "document_number": "DOC-1",
                "email": "cliente@example.test",
                "phone": "555-0200",
                "address": "Dirección",
                "notes": "Nota",
                "is_active": False,
            },
            Customer,
        ),
    ],
)
def test_partner_forms_exact_fields_bootstrap_autocomplete_valid_and_ignore_status(
    form_class, fields, data, model
):
    form = form_class(data=data)

    assert list(form.fields) == fields
    assert all(field.widget.attrs["class"] == "form-control" for field in form.fields.values())
    assert form.fields["email"].widget.attrs["autocomplete"] == "email"
    assert form.fields["phone"].widget.attrs["autocomplete"] == "tel"
    assert form.is_valid(), form.errors
    instance = form.save()
    assert model.objects.filter(pk=instance.pk).exists()
    assert instance.is_active is True


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("form_class", "identifier", "model"),
    [(SupplierForm, "tax_id", Supplier), (CustomerForm, "document_number", Customer)],
)
def test_partner_forms_reject_blank_invalid_email_and_normalized_duplicate(
    form_class, identifier, model
):
    model.objects.create(name="Existente", **{identifier: "ID-1"})
    data = {
        "name": " ",
        identifier: " id-1 ",
        "email": "correo-invalido",
        "phone": "",
        "address": "",
        "notes": "",
    }
    if form_class is SupplierForm:
        data["contact_name"] = ""
    form = form_class(data=data)

    assert not form.is_valid()
    assert {"name", identifier, "email"} <= set(form.errors)
    assert "constraint" not in str(form.errors).lower()
