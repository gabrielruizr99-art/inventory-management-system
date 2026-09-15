import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test import Client
from django.urls import reverse

from accounts.forms import BootstrapAuthenticationForm

User = get_user_model()
TEST_ONLY_PASSWORD = "test-only-password-123"
INCORRECT_TEST_ONLY_PASSWORD = "incorrect-test-only-password"


@pytest.mark.django_db
def test_auth_user_model():
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert User.__name__ == "User"
    assert User._meta.app_label == "accounts"


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(username="testuser", password=TEST_ONLY_PASSWORD)
    assert user.username == "testuser"
    assert user.check_password(TEST_ONLY_PASSWORD)


@pytest.mark.django_db
def test_groups_exist():
    expected_groups = ["Administrador", "Vendedor", "Almacén"]
    for name in expected_groups:
        assert Group.objects.filter(name=name).exists()


@pytest.mark.django_db
def test_test_database_is_isolated_and_uses_postgresql():
    database_name = str(connection.settings_dict["NAME"])

    assert connection.vendor == "postgresql"
    assert database_name != "inventory_management"
    assert database_name.startswith("test_")


def test_login_form_uses_bootstrap_and_autocomplete_attributes():
    form = BootstrapAuthenticationForm()

    assert form.fields["username"].widget.attrs["class"] == "form-control"
    assert form.fields["username"].widget.attrs["autocomplete"] == "username"
    assert form.fields["username"].widget.attrs["autofocus"] is True
    assert form.fields["password"].widget.attrs["class"] == "form-control"
    assert form.fields["password"].widget.attrs["autocomplete"] == "current-password"


@pytest.mark.django_db
def test_login_valid_credentials(client: Client):
    User.objects.create_user(username="testuser", password=TEST_ONLY_PASSWORD)
    response = client.post(
        reverse("login"), {"username": "testuser", "password": TEST_ONLY_PASSWORD}
    )
    assert response.status_code == 302
    assert response.url == reverse("home")


@pytest.mark.django_db
def test_login_invalid_credentials(client: Client):
    User.objects.create_user(username="testuser", password=TEST_ONLY_PASSWORD)
    response = client.post(
        reverse("login"),
        {"username": "testuser", "password": INCORRECT_TEST_ONLY_PASSWORD},
    )
    assert response.status_code == 200
    assert "Usuario o contraseña incorrectos." in response.content.decode()


@pytest.mark.django_db
def test_logout_post(client: Client):
    User.objects.create_user(username="testuser", password=TEST_ONLY_PASSWORD)
    client.login(username="testuser", password=TEST_ONLY_PASSWORD)
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")


@pytest.mark.django_db
def test_logout_get_not_allowed(client: Client):
    User.objects.create_user(username="testuser", password=TEST_ONLY_PASSWORD)
    client.login(username="testuser", password=TEST_ONLY_PASSWORD)
    response = client.get(reverse("logout"))
    assert response.status_code == 405
