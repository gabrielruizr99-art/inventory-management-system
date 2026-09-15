from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import Client
from django.urls import reverse

from partners.models import Customer, Supplier

User = get_user_model()
TEST_ONLY_PASSWORD = "fictitious-test-only-password"


def role_user(role, suffix="user"):
    user = User.objects.create_user(username=f"{role}-{suffix}", password=TEST_ONLY_PASSWORD)
    user.groups.add(Group.objects.get(name=role))
    return user


@pytest.fixture
def partner_objects(db):
    return (
        Supplier.objects.create(name="Proveedor", tax_id="RUC-1", contact_name="Contacto"),
        Customer.objects.create(
            name="Cliente", document_number="DOC-1", email="cliente@example.test"
        ),
    )


def partner_urls(supplier, customer):
    return [
        reverse("partners:supplier_list"),
        reverse("partners:supplier_detail", args=[supplier.pk]),
        reverse("partners:supplier_create"),
        reverse("partners:supplier_update", args=[supplier.pk]),
        reverse("partners:supplier_status", args=[supplier.pk]),
        reverse("partners:supplier_delete", args=[supplier.pk]),
        reverse("partners:customer_list"),
        reverse("partners:customer_detail", args=[customer.pk]),
        reverse("partners:customer_create"),
        reverse("partners:customer_update", args=[customer.pk]),
        reverse("partners:customer_status", args=[customer.pk]),
        reverse("partners:customer_delete", args=[customer.pk]),
    ]


@pytest.mark.django_db
def test_partner_views_redirect_anonymous_with_next(partner_objects, client):
    supplier, customer = partner_objects
    for url in partner_urls(supplier, customer):
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={url}"


@pytest.mark.django_db
def test_partner_views_return_403_without_permission(partner_objects, client):
    supplier, customer = partner_objects
    client.force_login(User.objects.create_user(username="sin-permisos"))
    for url in partner_urls(supplier, customer):
        assert client.get(url).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "allowed_actions"),
    [
        ("Administrador", set(range(12))),
        ("Vendedor", {6, 7, 8, 9}),
        ("Almacén", {0, 1, 2, 3, 4}),
    ],
)
def test_partner_role_matrix_controls_endpoints(partner_objects, role, allowed_actions):
    supplier, customer = partner_objects
    client = Client()
    client.force_login(role_user(role))
    for index, url in enumerate(partner_urls(supplier, customer)):
        response = client.get(url)
        if index in {4, 10} and index in allowed_actions:
            assert response.status_code == 405
        else:
            assert response.status_code == (200 if index in allowed_actions else 403)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("entity", "model", "payload", "created_name"),
    [
        (
            "supplier",
            Supplier,
            {
                "name": "Nuevo proveedor",
                "tax_id": "RUC-2",
                "contact_name": "Contacto",
                "email": "p@example.test",
                "phone": "1",
                "address": "Dirección",
                "notes": "Nota",
            },
            "Nuevo proveedor",
        ),
        (
            "customer",
            Customer,
            {
                "name": "Nuevo cliente",
                "document_number": "DOC-2",
                "email": "c@example.test",
                "phone": "2",
                "address": "Dirección",
                "notes": "Nota",
            },
            "Nuevo cliente",
        ),
    ],
)
def test_partner_crud_status_messages_and_404(entity, model, payload, created_name):
    client = Client()
    client.force_login(role_user("Administrador", entity))
    assert client.get(reverse(f"partners:{entity}_list")).status_code == 200
    created = client.post(reverse(f"partners:{entity}_create"), payload, follow=True)
    assert "creado correctamente" in created.content.decode()
    instance = model.objects.get(name=created_name)
    assert client.get(reverse(f"partners:{entity}_detail", args=[instance.pk])).status_code == 200
    payload["name"] = f"{created_name} actualizado"
    updated = client.post(
        reverse(f"partners:{entity}_update", args=[instance.pk]), payload, follow=True
    )
    assert "actualizado correctamente" in updated.content.decode()
    status = client.post(reverse(f"partners:{entity}_status", args=[instance.pk]), follow=True)
    instance.refresh_from_db()
    assert not instance.is_active
    assert "Estado" in status.content.decode()
    deleted = client.post(reverse(f"partners:{entity}_delete", args=[instance.pk]), follow=True)
    assert not model.objects.filter(pk=instance.pk).exists()
    assert "eliminado correctamente" in deleted.content.decode()
    for action in ("detail", "update", "status", "delete"):
        method = client.post if action == "status" else client.get
        assert method(reverse(f"partners:{entity}_{action}", args=[999999])).status_code == 404


@pytest.mark.django_db
def test_partner_lists_search_filter_empty_invalid_and_pagination(partner_objects):
    supplier, customer = partner_objects
    Supplier.objects.create(name="Archivado", is_active=False)
    client = Client()
    client.force_login(role_user("Administrador"))
    for index in range(21):
        Supplier.objects.create(name=f"Proveedor {index:02}")

    result = client.get(reverse("partners:supplier_list"), {"q": "RUC-1", "status": "active"})
    assert supplier in result.context["suppliers"]
    page = client.get(reverse("partners:supplier_list"), {"q": "Proveedor", "page": 2})
    assert page.context["is_paginated"]
    assert "q=Proveedor&amp;page=1" in page.content.decode()
    assert client.get(reverse("partners:supplier_list"), {"status": "invalid"}).status_code == 200
    customer_result = client.get(reverse("partners:customer_list"), {"q": "DOC-1"})
    assert list(customer_result.context["customers"]) == [customer]
    empty = client.get(reverse("partners:customer_list"), {"q": "No existe"})
    assert "No hay clientes" in empty.content.decode()


@pytest.mark.django_db
def test_partner_status_and_delete_enforce_methods_and_csrf(partner_objects):
    supplier, _ = partner_objects
    client = Client(enforce_csrf_checks=True)
    client.force_login(role_user("Administrador"))
    status_url = reverse("partners:supplier_status", args=[supplier.pk])
    delete_url = reverse("partners:supplier_delete", args=[supplier.pk])

    assert client.get(status_url).status_code == 405
    assert client.post(status_url).status_code == 403
    detail = client.get(reverse("partners:supplier_detail", args=[supplier.pk]))
    token = detail.cookies["csrftoken"].value
    assert client.post(status_url, {"csrfmiddlewaretoken": token}).status_code == 302
    confirmation = client.get(delete_url)
    assert Supplier.objects.filter(pk=supplier.pk).exists()
    token = confirmation.cookies["csrftoken"].value
    assert client.post(delete_url).status_code == 403
    assert client.post(delete_url, {"csrfmiddlewaretoken": token}).status_code == 302


@pytest.mark.django_db
def test_partner_create_race_and_protected_delete_are_handled(partner_objects):
    supplier, _ = partner_objects
    client = Client()
    client.force_login(role_user("Administrador"))
    with patch("partners.forms.CustomerForm.save", side_effect=IntegrityError("detalle SQL")):
        response = client.post(
            reverse("partners:customer_create"),
            {
                "name": "Cliente",
                "document_number": "DOC-2",
                "email": "",
                "phone": "",
                "address": "",
                "notes": "",
            },
        )
    assert response.status_code == 200
    assert "coinciden con otro existente" in response.content.decode()
    assert "detalle SQL" not in response.content.decode()

    with patch.object(
        Supplier,
        "delete",
        side_effect=ProtectedError("Relación protegida de prueba", {supplier}),
    ):
        protected = client.post(
            reverse("partners:supplier_delete", args=[supplier.pk]), follow=True
        )
    assert protected.status_code == 200
    assert "No se puede eliminar" in protected.content.decode()
    assert Supplier.objects.filter(pk=supplier.pk).exists()
