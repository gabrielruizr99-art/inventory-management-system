from decimal import Decimal

import pytest

from catalog.forms import CategoryForm, ProductForm
from catalog.models import Category, Product


@pytest.mark.django_db
def test_category_form_fields_bootstrap_autocomplete_and_unauthorized_fields():
    form = CategoryForm(data={"name": "Nueva", "description": "Texto", "is_active": False})

    assert list(form.fields) == ["name", "description"]
    assert all(field.widget.attrs["class"] == "form-control" for field in form.fields.values())
    assert form.fields["name"].widget.attrs["autocomplete"] == "organization-title"
    assert form.is_valid()
    category = form.save()
    assert category.is_active is True


@pytest.mark.django_db
def test_category_form_rejects_blank_and_normalized_duplicate():
    Category.objects.create(name="Alimentos")

    assert not CategoryForm(data={"name": " ", "description": ""}).is_valid()
    duplicate = CategoryForm(data={"name": " alimentos ", "description": ""})
    assert not duplicate.is_valid()
    assert "constraint" not in str(duplicate.errors).lower()


@pytest.mark.django_db
def test_product_form_fields_bootstrap_valid_creation_and_unauthorized_fields():
    category = Category.objects.create(name="General")
    form = ProductForm(
        data={
            "sku": "sku-1",
            "barcode": "",
            "name": "Producto",
            "description": "Descripción",
            "category": category.pk,
            "unit_of_measure": Product.UnitOfMeasure.UNIT,
            "sale_price": "12.50",
            "is_active": False,
        }
    )

    assert list(form.fields) == [
        "sku",
        "barcode",
        "name",
        "description",
        "category",
        "unit_of_measure",
        "sale_price",
    ]
    assert form.fields["category"].widget.attrs["class"] == "form-select"
    assert form.fields["unit_of_measure"].widget.attrs["class"] == "form-select"
    assert form.fields["sku"].widget.attrs["autocomplete"] == "off"
    assert form.is_valid(), form.errors
    product = form.save()
    assert product.sale_price == Decimal("12.50")
    assert product.is_active is True


@pytest.mark.django_db
def test_product_form_rejects_invalid_data_duplicate_and_negative_price():
    category = Category.objects.create(name="General")
    Product.objects.create(
        sku="SKU-1",
        name="Existente",
        category=category,
        unit_of_measure="UNIT",
        sale_price=Decimal("1.00"),
    )
    invalid = ProductForm(
        data={
            "sku": " sku-1 ",
            "name": "Otro",
            "category": category.pk,
            "unit_of_measure": "UNIT",
            "sale_price": "-1",
        }
    )

    assert not invalid.is_valid()
    assert {"sku", "sale_price"} <= set(invalid.errors)
    assert "constraint" not in str(invalid.errors).lower()


@pytest.mark.django_db
def test_product_form_excludes_inactive_category_on_create_but_keeps_current_on_edit():
    active = Category.objects.create(name="Activa")
    inactive = Category.objects.create(name="Inactiva", is_active=False)
    product = Product.objects.create(
        sku="SKU-1",
        name="Producto",
        category=inactive,
        unit_of_measure="UNIT",
        sale_price=Decimal("1.00"),
    )

    create_ids = set(ProductForm().fields["category"].queryset.values_list("pk", flat=True))
    edit_ids = set(
        ProductForm(instance=product).fields["category"].queryset.values_list("pk", flat=True)
    )

    assert create_ids == {active.pk}
    assert edit_ids == {active.pk, inactive.pk}


@pytest.mark.django_db
def test_product_form_reports_normalized_duplicate_barcode_on_the_field():
    category = Category.objects.create(name="General")
    Product.objects.create(
        sku="SKU-1",
        barcode="BAR-1",
        name="Existente",
        category=category,
        unit_of_measure="UNIT",
        sale_price=Decimal("1.00"),
    )
    form = ProductForm(
        data={
            "sku": "SKU-2",
            "barcode": " BAR-1 ",
            "name": "Otro",
            "category": category.pk,
            "unit_of_measure": "UNIT",
            "sale_price": "1.00",
        }
    )

    assert not form.is_valid()
    assert "barcode" in form.errors
    assert "constraint" not in str(form.errors).lower()
