from decimal import Decimal

import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from catalog.admin import CategoryAdmin, ProductAdmin
from catalog.models import Category, Product


@pytest.fixture
def category():
    return Category.objects.create(name="Herramientas")


@pytest.mark.django_db
def test_category_creation_defaults_normalization_and_string():
    category = Category.objects.create(
        name="  Ferretería  ",
        description="  Productos de ferretería  ",
    )

    assert category.name == "Ferretería"
    assert category.description == "Productos de ferretería"
    assert category.is_active is True
    assert str(category) == "Ferretería"
    assert category.created_at is not None
    assert category.updated_at is not None


@pytest.mark.django_db
def test_category_default_ordering():
    Category.objects.create(name="Zeta")
    Category.objects.create(name="Alfa")

    assert list(Category.objects.values_list("name", flat=True)) == ["Alfa", "Zeta"]


def test_category_model_validation_rejects_blank_name():
    with pytest.raises(ValidationError, match="nombre de la categoría"):
        Category(name="   ").full_clean()


@pytest.mark.django_db
def test_category_database_rejects_normalized_duplicate_and_blank_name():
    Category.objects.create(name="Ferretería")

    with pytest.raises(IntegrityError), transaction.atomic():
        Category.objects.bulk_create([Category(name="  ferretería  ")])
    with pytest.raises(IntegrityError), transaction.atomic():
        Category.objects.bulk_create([Category(name="   ")])


@pytest.mark.django_db
def test_product_creation_defaults_normalization_and_string(category):
    product = Product.objects.create(
        sku="  sku-001  ",
        barcode=" 0012345678905 ",
        name="  Martillo  ",
        description="  Mango reforzado  ",
        category=category,
        sale_price=Decimal("25.50"),
    )

    assert product.sku == "SKU-001"
    assert product.barcode == "0012345678905"
    assert product.name == "Martillo"
    assert product.description == "Mango reforzado"
    assert product.unit_of_measure == Product.UnitOfMeasure.UNIT
    assert product.is_active is True
    assert str(product) == "SKU-001 — Martillo"


@pytest.mark.django_db
def test_product_default_ordering(category):
    Product.objects.create(sku="Z-1", name="Zeta", category=category, sale_price=1)
    Product.objects.create(sku="A-2", name="Alfa", category=category, sale_price=1)
    Product.objects.create(sku="A-1", name="Alfa", category=category, sale_price=1)

    assert list(Product.objects.values_list("sku", flat=True)) == ["A-1", "A-2", "Z-1"]


@pytest.mark.django_db
def test_product_zero_price_and_valid_choices_are_allowed(category):
    for index, unit in enumerate(Product.UnitOfMeasure.values):
        product = Product(
            sku=f"UNIT-{index}",
            name=f"Producto {index}",
            category=category,
            unit_of_measure=unit,
            sale_price=Decimal("0.00"),
        )
        product.full_clean()
        product.save()

    assert Product.objects.count() == len(Product.UnitOfMeasure.values)


@pytest.mark.django_db
def test_product_model_validation_rejects_required_fields_negative_price_and_invalid_unit(
    category,
):
    product = Product(
        sku=" ",
        name=" ",
        category=category,
        unit_of_measure="INVALID",
        sale_price=Decimal("-0.01"),
    )

    with pytest.raises(ValidationError) as error:
        product.full_clean()

    assert {"sku", "name", "unit_of_measure", "sale_price"} <= set(error.value.message_dict)


@pytest.mark.django_db
def test_product_database_constraints_reject_invalid_values(category):
    invalid_products = [
        Product(sku=" ", name="Válido", category=category, sale_price=1),
        Product(sku="NAME-X", name=" ", category=category, sale_price=1),
        Product(
            sku="BARCODE-X",
            barcode=" ",
            name="Válido",
            category=category,
            sale_price=1,
        ),
        Product(sku="NEG", name="Válido", category=category, sale_price=Decimal("-0.01")),
        Product(
            sku="UNIT-X",
            name="Válido",
            category=category,
            unit_of_measure="INVALID",
            sale_price=1,
        ),
    ]

    for product in invalid_products:
        with pytest.raises(IntegrityError), transaction.atomic():
            Product.objects.bulk_create([product])


@pytest.mark.django_db
def test_product_sku_and_barcode_database_uniqueness_are_normalized(category):
    Product.objects.create(
        sku="SKU-001",
        barcode="0012345678905",
        name="Primero",
        category=category,
        sale_price=1,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.bulk_create(
            [Product(sku=" sku-001 ", name="Segundo", category=category, sale_price=1)]
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.bulk_create(
            [
                Product(
                    sku="SKU-002",
                    barcode=" 0012345678905 ",
                    name="Segundo",
                    category=category,
                    sale_price=1,
                )
            ]
        )


@pytest.mark.django_db
def test_product_allows_multiple_empty_barcodes(category):
    Product.objects.create(sku="SKU-001", name="Uno", category=category, sale_price=1)
    Product.objects.create(sku="SKU-002", name="Dos", category=category, sale_price=1)

    assert Product.objects.filter(barcode="").count() == 2


@pytest.mark.django_db
def test_product_category_is_protected(category):
    Product.objects.create(sku="SKU-001", name="Uno", category=category, sale_price=1)

    with pytest.raises(ProtectedError):
        category.delete()


def test_catalog_constraints_indexes_and_admin_registration():
    category_constraints = {constraint.name for constraint in Category._meta.constraints}
    product_constraints = {constraint.name for constraint in Product._meta.constraints}

    assert "catalog_category_name_ci_uniq" in category_constraints
    assert "catalog_product_sku_ci_uniq" in product_constraints
    assert "catalog_product_barcode_uniq" in product_constraints
    assert "catalog_product_sale_price_nonnegative" in product_constraints
    assert [index.name for index in Product._meta.indexes] == ["cat_product_cat_active_idx"]
    assert isinstance(admin.site._registry[Category], CategoryAdmin)
    assert isinstance(admin.site._registry[Product], ProductAdmin)
