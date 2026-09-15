from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("locations/", views.LocationListView.as_view(), name="location_list"),
    path("locations/create/", views.LocationCreateView.as_view(), name="location_create"),
    path("locations/<int:pk>/", views.LocationDetailView.as_view(), name="location_detail"),
    path("locations/<int:pk>/edit/", views.LocationUpdateView.as_view(), name="location_update"),
    path("locations/<int:pk>/status/", views.LocationStatusView.as_view(), name="location_status"),
    path("locations/<int:pk>/delete/", views.LocationDeleteView.as_view(), name="location_delete"),
]
