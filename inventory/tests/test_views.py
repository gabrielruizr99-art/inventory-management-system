from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import Client
from django.urls import reverse

from inventory.models import Location

User = get_user_model()
TEST_ONLY_PASSWORD = "fictitious-test-only-password"


def role_user(role, suffix="user"):
    user = User.objects.create_user(username=f"{role}-{suffix}", password=TEST_ONLY_PASSWORD)
    user.groups.add(Group.objects.get(name=role))
    return user


@pytest.fixture
def location(db):
    return Location.objects.create(
        code="LOC-1", name="Ubicación central", location_type="WAREHOUSE", address="Centro"
    )


def location_urls(location):
    return [
        reverse("inventory:location_list"),
        reverse("inventory:location_detail", args=[location.pk]),
        reverse("inventory:location_create"),
        reverse("inventory:location_update", args=[location.pk]),
        reverse("inventory:location_status", args=[location.pk]),
        reverse("inventory:location_delete", args=[location.pk]),
    ]


@pytest.mark.django_db
def test_location_views_redirect_anonymous_with_next(location, client):
    for url in location_urls(location):
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={url}"


@pytest.mark.django_db
def test_location_views_return_403_without_permission(location, client):
    client.force_login(User.objects.create_user(username="sin-permisos"))
    for url in location_urls(location):
        assert client.get(url).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "allowed_actions"),
    [
        ("Administrador", set(range(6))),
        ("Vendedor", {0, 1}),
        ("Almacén", {0, 1}),
    ],
)
def test_location_role_matrix_controls_endpoints(location, role, allowed_actions):
    client = Client()
    client.force_login(role_user(role))
    for index, url in enumerate(location_urls(location)):
        response = client.get(url)
        if index == 4 and index in allowed_actions:
            assert response.status_code == 405
        else:
            assert response.status_code == (200 if index in allowed_actions else 403)


@pytest.mark.django_db
def test_location_crud_status_messages_and_404(location):
    client = Client()
    client.force_login(role_user("Administrador"))
    payload = {
        "code": "LOC-2",
        "name": "Nueva ubicación",
        "location_type": "BRANCH",
        "address": "Norte",
    }

    assert client.get(reverse("inventory:location_list")).status_code == 200
    assert client.get(reverse("inventory:location_detail", args=[location.pk])).status_code == 200
    created = client.post(reverse("inventory:location_create"), payload, follow=True)
    assert "Ubicación creada correctamente." in created.content.decode()
    new_location = Location.objects.get(code="LOC-2")
    payload["name"] = "Ubicación actualizada"
    updated = client.post(
        reverse("inventory:location_update", args=[new_location.pk]), payload, follow=True
    )
    assert "Ubicación actualizada correctamente." in updated.content.decode()
    status = client.post(reverse("inventory:location_status", args=[new_location.pk]), follow=True)
    new_location.refresh_from_db()
    assert not new_location.is_active
    assert "Estado de la ubicación actualizado correctamente." in status.content.decode()
    deleted = client.post(reverse("inventory:location_delete", args=[new_location.pk]), follow=True)
    assert not Location.objects.filter(pk=new_location.pk).exists()
    assert "Ubicación eliminada correctamente." in deleted.content.decode()
    for action in ("detail", "update", "status", "delete"):
        method = client.post if action == "status" else client.get
        assert method(reverse(f"inventory:location_{action}", args=[999999])).status_code == 404


@pytest.mark.django_db
def test_location_list_search_filters_empty_invalid_and_pagination(location):
    inactive = Location.objects.create(
        code="LOC-2", name="Archivada", location_type="BRANCH", is_active=False
    )
    client = Client()
    client.force_login(role_user("Administrador"))
    for index in range(21):
        Location.objects.create(
            code=f"P-{index:02}", name=f"Paginada {index:02}", location_type="BRANCH"
        )

    result = client.get(
        reverse("inventory:location_list"),
        {"q": "Archivada", "status": "inactive", "type": "BRANCH"},
    )
    assert list(result.context["locations"]) == [inactive]
    page = client.get(reverse("inventory:location_list"), {"q": "Paginada", "page": 2})
    assert page.context["is_paginated"]
    assert "q=Paginada&amp;page=1" in page.content.decode()
    invalid = client.get(reverse("inventory:location_list"), {"status": "bad", "type": "bad"})
    assert invalid.status_code == 200
    empty = client.get(reverse("inventory:location_list"), {"q": "No existe"})
    assert "No hay ubicaciones" in empty.content.decode()
    assert (
        location
        in client.get(reverse("inventory:location_list"), {"q": "Centro"}).context["locations"]
    )


@pytest.mark.django_db
def test_location_status_delete_csrf_get_confirmation_and_protected_error(location):
    client = Client(enforce_csrf_checks=True)
    client.force_login(role_user("Administrador"))
    status_url = reverse("inventory:location_status", args=[location.pk])
    delete_url = reverse("inventory:location_delete", args=[location.pk])

    assert client.get(status_url).status_code == 405
    assert client.post(status_url).status_code == 403
    detail = client.get(reverse("inventory:location_detail", args=[location.pk]))
    token = detail.cookies["csrftoken"].value
    assert client.post(status_url, {"csrfmiddlewaretoken": token}).status_code == 302
    confirmation = client.get(delete_url)
    assert confirmation.status_code == 200
    assert Location.objects.filter(pk=location.pk).exists()
    token = confirmation.cookies["csrftoken"].value
    assert client.post(delete_url).status_code == 403
    with patch.object(
        Location,
        "delete",
        side_effect=ProtectedError("Relación protegida de prueba", {location}),
    ):
        protected = client.post(delete_url, {"csrfmiddlewaretoken": token}, follow=True)
    assert protected.status_code == 200
    assert "No se puede eliminar" in protected.content.decode()
    assert Location.objects.filter(pk=location.pk).exists()


@pytest.mark.django_db
def test_location_create_handles_database_race_without_exposing_details(location):
    client = Client()
    client.force_login(role_user("Administrador"))
    with patch("inventory.forms.LocationForm.save", side_effect=IntegrityError("detalle SQL")):
        response = client.post(
            reverse("inventory:location_create"),
            {"code": "LOC-2", "name": "Nueva", "location_type": "BRANCH", "address": ""},
        )

    content = response.content.decode()
    assert response.status_code == 200
    assert "coinciden con otra existente" in content
    assert "detalle SQL" not in content
