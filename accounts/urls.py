from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import BootstrapAuthenticationForm

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            authentication_form=BootstrapAuthenticationForm,
            template_name="registration/login.html",
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]
