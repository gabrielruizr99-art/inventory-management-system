import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from partners.admin import CustomerAdmin, SupplierAdmin
from partners.models import Customer, Supplier


@pytest.mark.django_db
def test_supplier_creation_defaults_normalization_and_string():
    supplier = Supplier.objects.create(
        name="  Proveedor Central  ",
        tax_id="  ruc-001  ",
        contact_name="  Contacto  ",
        email="  contacto@example.test  ",
        phone="  +51 900 000 000  ",
        address="  Dirección de prueba  ",
        notes="  Nota de prueba  ",
    )

    assert supplier.name == "Proveedor Central"
    assert supplier.tax_id == "RUC-001"
    assert supplier.contact_name == "Contacto"
    assert supplier.email == "contacto@example.test"
    assert supplier.phone == "+51 900 000 000"
    assert supplier.address == "Dirección de prueba"
    assert supplier.notes == "Nota de prueba"
    assert supplier.is_active is True
    assert str(supplier) == "Proveedor Central"


@pytest.mark.django_db
def test_customer_creation_defaults_normalization_and_string():
    customer = Customer.objects.create(
        name="  Cliente de prueba  ",
        document_number="  doc-001  ",
        email="  cliente@example.test  ",
        phone="  555-0100  ",
        address="  Dirección de prueba  ",
        notes="  Nota de prueba  ",
    )

    assert customer.name == "Cliente de prueba"
    assert customer.document_number == "DOC-001"
    assert customer.email == "cliente@example.test"
    assert customer.phone == "555-0100"
    assert customer.address == "Dirección de prueba"
    assert customer.notes == "Nota de prueba"
    assert customer.is_active is True
    assert str(customer) == "Cliente de prueba"


@pytest.mark.django_db
def test_partner_names_may_be_duplicated_and_are_ordered():
    Supplier.objects.create(name="Zeta")
    Supplier.objects.create(name="Duplicado")
    Supplier.objects.create(name="Duplicado")
    Supplier.objects.create(name="Alfa")
    Customer.objects.create(name="Zeta")
    Customer.objects.create(name="Alfa")

    assert list(Supplier.objects.values_list("name", flat=True)) == [
        "Alfa",
        "Duplicado",
        "Duplicado",
        "Zeta",
    ]
    assert list(Customer.objects.values_list("name", flat=True)) == ["Alfa", "Zeta"]


@pytest.mark.django_db
def test_optional_partner_identifiers_allow_multiple_empty_values():
    Supplier.objects.create(name="Proveedor uno")
    Supplier.objects.create(name="Proveedor dos")
    Customer.objects.create(name="Cliente uno")
    Customer.objects.create(name="Cliente dos")

    assert Supplier.objects.filter(tax_id="").count() == 2
    assert Customer.objects.filter(document_number="").count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("model", [Supplier, Customer])
def test_partner_model_validation_rejects_blank_names_and_invalid_emails(model):
    partner = model(name="   ", email="invalid-email")

    with pytest.raises(ValidationError) as error:
        partner.full_clean()

    assert {"name", "email"} <= set(error.value.message_dict)


@pytest.mark.django_db
def test_partner_database_rejects_blank_names():
    invalid_partners = (
        Supplier(name="   "),
        Customer(name="   "),
        Supplier(name="Válido", tax_id="   "),
        Customer(name="Válido", document_number="   "),
    )

    for partner in invalid_partners:
        with pytest.raises(IntegrityError), transaction.atomic():
            partner.__class__.objects.bulk_create([partner])


@pytest.mark.django_db
def test_supplier_tax_id_database_uniqueness_is_normalized():
    Supplier.objects.create(name="Primero", tax_id="RUC-001")

    with pytest.raises(IntegrityError), transaction.atomic():
        Supplier.objects.bulk_create([Supplier(name="Segundo", tax_id=" ruc-001 ")])


@pytest.mark.django_db
def test_customer_document_database_uniqueness_is_normalized():
    Customer.objects.create(name="Primero", document_number="DOC-001")

    with pytest.raises(IntegrityError), transaction.atomic():
        Customer.objects.bulk_create([Customer(name="Segundo", document_number=" doc-001 ")])


def test_partner_constraints_and_admin_registration():
    supplier_constraints = {constraint.name for constraint in Supplier._meta.constraints}
    customer_constraints = {constraint.name for constraint in Customer._meta.constraints}

    assert "partners_supplier_tax_id_ci_uniq" in supplier_constraints
    assert "partners_customer_document_ci_uniq" in customer_constraints
    assert isinstance(admin.site._registry[Supplier], SupplierAdmin)
    assert isinstance(admin.site._registry[Customer], CustomerAdmin)
