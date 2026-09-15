import pytest
from django.contrib.auth import get_user_model
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
