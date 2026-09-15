import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

User = get_user_model()
TEST_ONLY_PASSWORD = "test-only-password-123"


@pytest.mark.django_db
def test_home_redirects_anonymous(client: Client):
    response = client.get(reverse("home"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_home_authenticated(client: Client):
    User.objects.create_user(username="testuser", password=TEST_ONLY_PASSWORD)
    client.login(username="testuser", password=TEST_ONLY_PASSWORD)
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert "Dashboard Principal" in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "visible", "hidden"),
    [
        (
            "Administrador",
            ["Categorías", "Productos", "Proveedores", "Clientes", "Ubicaciones"],
            [],
        ),
        (
            "Vendedor",
            ["Categorías", "Productos", "Clientes", "Ubicaciones"],
            ["Proveedores"],
        ),
        (
            "Almacén",
            ["Categorías", "Productos", "Proveedores", "Ubicaciones"],
            ["Clientes"],
        ),
    ],
)
def test_navigation_links_follow_effective_role_permissions(client: Client, role, visible, hidden):
    user = User.objects.create_user(username=f"nav-{role}", password=TEST_ONLY_PASSWORD)
    user.groups.add(Group.objects.get(name=role))
    client.force_login(user)

    content = client.get(reverse("home")).content.decode()

    for label in visible:
        assert f">{label}</a>" in content
    for label in hidden:
        assert f">{label}</a>" not in content


@pytest.mark.django_db
def test_navigation_hides_master_data_links_without_permissions(client: Client):
    user = User.objects.create_user(username="nav-sin-permisos", password=TEST_ONLY_PASSWORD)
    client.force_login(user)

    content = client.get(reverse("home")).content.decode()

    for label in ("Categorías", "Productos", "Proveedores", "Clientes", "Ubicaciones"):
        assert f">{label}</a>" not in content
