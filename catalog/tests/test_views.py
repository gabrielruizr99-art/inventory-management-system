from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse

from catalog.models import Category, Product

User = get_user_model()
TEST_ONLY_PASSWORD = "fictitious-test-only-password"


def role_user(role, suffix="user"):
    user = User.objects.create_user(username=f"{role}-{suffix}", password=TEST_ONLY_PASSWORD)
    user.groups.add(Group.objects.get(name=role))
    return user


@pytest.fixture
def catalog_objects(db):
    category = Category.objects.create(name="General")
    product = Product.objects.create(
        sku="SKU-1",
        barcode="BAR-1",
        name="Producto",
        category=category,
        unit_of_measure="UNIT",
        sale_price=Decimal("10.00"),
    )
    return category, product


def catalog_urls(category, product):
    return [
        reverse("catalog:category_list"),
        reverse("catalog:category_detail", args=[category.pk]),
        reverse("catalog:category_create"),
        reverse("catalog:category_update", args=[category.pk]),
        reverse("catalog:category_status", args=[category.pk]),
        reverse("catalog:category_delete", args=[category.pk]),
        reverse("catalog:product_list"),
        reverse("catalog:product_detail", args=[product.pk]),
        reverse("catalog:product_create"),
        reverse("catalog:product_update", args=[product.pk]),
        reverse("catalog:product_status", args=[product.pk]),
        reverse("catalog:product_delete", args=[product.pk]),
    ]


@pytest.mark.django_db
def test_catalog_views_redirect_anonymous_with_next(catalog_objects, client):
    category, product = catalog_objects
    for url in catalog_urls(category, product):
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={url}"


@pytest.mark.django_db
def test_catalog_views_return_403_without_permission(catalog_objects, client):
    category, product = catalog_objects
    user = User.objects.create_user(username="sin-permisos", password=TEST_ONLY_PASSWORD)
    client.force_login(user)

    for url in catalog_urls(category, product):
        assert client.get(url).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "allowed_actions"),
    [
        ("Administrador", set(range(12))),
        ("Vendedor", {0, 1, 6, 7}),
        ("Almacén", {0, 1, 2, 3, 4, 6, 7, 8, 9, 10}),
    ],
)
def test_catalog_role_matrix_controls_endpoints(catalog_objects, role, allowed_actions):
    category, product = catalog_objects
    client = Client()
    client.force_login(role_user(role))

    for index, url in enumerate(catalog_urls(category, product)):
        response = client.get(url)
        if index in {4, 10} and index in allowed_actions:
            assert response.status_code == 405
        else:
            assert response.status_code == (200 if index in allowed_actions else 403)


@pytest.mark.django_db
def test_category_crud_status_messages_404_and_protected_delete(catalog_objects):
    category, product = catalog_objects
    client = Client()
    client.force_login(role_user("Administrador"))

    assert client.get(reverse("catalog:category_list")).status_code == 200
    assert client.get(reverse("catalog:category_detail", args=[category.pk])).status_code == 200
    created = client.post(
        reverse("catalog:category_create"), {"name": "Nueva", "description": "Texto"}, follow=True
    )
    assert created.status_code == 200
    assert "Categoría creada correctamente." in created.content.decode()
    new_category = Category.objects.get(name="Nueva")
    updated = client.post(
        reverse("catalog:category_update", args=[new_category.pk]),
        {"name": "Actualizada", "description": "Texto"},
        follow=True,
    )
    assert "Categoría actualizada correctamente." in updated.content.decode()
    status = client.post(reverse("catalog:category_status", args=[new_category.pk]), follow=True)
    new_category.refresh_from_db()
    assert not new_category.is_active
    assert "Estado de la categoría actualizado correctamente." in status.content.decode()
    deleted = client.post(reverse("catalog:category_delete", args=[new_category.pk]), follow=True)
    assert not Category.objects.filter(pk=new_category.pk).exists()
    assert "Categoría eliminada correctamente." in deleted.content.decode()
    protected = client.post(reverse("catalog:category_delete", args=[category.pk]), follow=True)
    assert Category.objects.filter(pk=category.pk).exists()
    assert "No se puede eliminar" in protected.content.decode()
    assert product.category_id == category.pk
    for name in ("category_detail", "category_update", "category_status", "category_delete"):
        method = client.post if name == "category_status" else client.get
        assert method(reverse(f"catalog:{name}", args=[999999])).status_code == 404


@pytest.mark.django_db
def test_product_crud_status_messages_and_404(catalog_objects):
    category, product = catalog_objects
    client = Client()
    client.force_login(role_user("Administrador"))
    payload = {
        "sku": "SKU-2",
        "barcode": "BAR-2",
        "name": "Nuevo",
        "description": "Texto",
        "category": category.pk,
        "unit_of_measure": "UNIT",
        "sale_price": "5.00",
    }

    assert client.get(reverse("catalog:product_list")).status_code == 200
    assert client.get(reverse("catalog:product_detail", args=[product.pk])).status_code == 200
    created = client.post(reverse("catalog:product_create"), payload, follow=True)
    assert "Producto creado correctamente." in created.content.decode()
    new_product = Product.objects.get(sku="SKU-2")
    payload["name"] = "Actualizado"
    updated = client.post(
        reverse("catalog:product_update", args=[new_product.pk]), payload, follow=True
    )
    assert "Producto actualizado correctamente." in updated.content.decode()
    status = client.post(reverse("catalog:product_status", args=[new_product.pk]), follow=True)
    new_product.refresh_from_db()
    assert not new_product.is_active
    assert "Estado del producto actualizado correctamente." in status.content.decode()
    deleted = client.post(reverse("catalog:product_delete", args=[new_product.pk]), follow=True)
    assert not Product.objects.filter(pk=new_product.pk).exists()
    assert "Producto eliminado correctamente." in deleted.content.decode()
    for name in ("product_detail", "product_update", "product_status", "product_delete"):
        method = client.post if name == "product_status" else client.get
        assert method(reverse(f"catalog:{name}", args=[999999])).status_code == 404


@pytest.mark.django_db
def test_catalog_lists_search_filter_empty_invalid_and_pagination(catalog_objects):
    category, product = catalog_objects
    inactive = Category.objects.create(name="Archivada", is_active=False)
    client = Client()
    client.force_login(role_user("Administrador"))
    for index in range(21):
        Category.objects.create(name=f"Categoría {index:02}")

    search = client.get(reverse("catalog:category_list"), {"q": "Archivada", "status": "inactive"})
    assert list(search.context["categories"]) == [inactive]
    empty = client.get(reverse("catalog:category_list"), {"q": "No existe"})
    assert "No hay categorías" in empty.content.decode()
    page = client.get(reverse("catalog:category_list"), {"q": "Categoría", "page": 2})
    assert page.context["is_paginated"]
    assert "q=Categor%C3%ADa&amp;page=1" in page.content.decode()
    invalid = client.get(reverse("catalog:category_list"), {"status": "unknown"})
    assert invalid.status_code == 200
    filtered = client.get(
        reverse("catalog:product_list"),
        {"q": "BAR-1", "category": category.pk, "unit": "UNIT", "status": "active"},
    )
    assert list(filtered.context["products"]) == [product]
    assert (
        client.get(reverse("catalog:product_list"), {"category": "bad", "unit": "bad"}).status_code
        == 200
    )


@pytest.mark.django_db
def test_catalog_status_and_delete_enforce_http_methods_and_csrf(catalog_objects):
    category, product = catalog_objects
    client = Client(enforce_csrf_checks=True)
    client.force_login(role_user("Administrador"))
    status_url = reverse("catalog:product_status", args=[product.pk])
    delete_url = reverse("catalog:product_delete", args=[product.pk])

    assert client.get(status_url).status_code == 405
    assert client.post(status_url).status_code == 403
    detail = client.get(reverse("catalog:product_detail", args=[product.pk]))
    token = detail.cookies["csrftoken"].value
    assert client.post(status_url, {"csrfmiddlewaretoken": token}).status_code == 302
    product.refresh_from_db()
    assert not product.is_active
    confirmation = client.get(delete_url)
    assert confirmation.status_code == 200
    assert Product.objects.filter(pk=product.pk).exists()
    token = confirmation.cookies["csrftoken"].value
    assert Client(enforce_csrf_checks=True).post(delete_url).status_code == 403
    assert client.post(delete_url).status_code == 403
    assert client.post(delete_url, {"csrfmiddlewaretoken": token}).status_code == 302
    assert not Product.objects.filter(pk=product.pk).exists()


@pytest.mark.django_db
def test_catalog_create_handles_database_race_without_exposing_details(catalog_objects):
    client = Client()
    client.force_login(role_user("Administrador"))
    with patch("catalog.forms.CategoryForm.save", side_effect=IntegrityError("detalle SQL")):
        response = client.post(
            reverse("catalog:category_create"), {"name": "Nueva", "description": ""}
        )

    content = response.content.decode()
    assert response.status_code == 200
    assert "coinciden con otro existente" in content
    assert "detalle SQL" not in content
