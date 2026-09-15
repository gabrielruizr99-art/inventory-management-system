from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import LocationForm
from .models import Location


class ProtectedPermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name()
            )
        raise PermissionDenied


class LocationListView(ProtectedPermissionMixin, ListView):
    model = Location
    permission_required = "inventory.view_location"
    template_name = "inventory/location_list.html"
    context_object_name = "locations"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(code__icontains=query) | Q(name__icontains=query) | Q(address__icontains=query)
            )
        status = self.request.GET.get("status", "")
        if status in {"active", "inactive"}:
            queryset = queryset.filter(is_active=status == "active")
        location_type = self.request.GET.get("type", "")
        if location_type in Location.LocationType.values:
            queryset = queryset.filter(location_type=location_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parameters = self.request.GET.copy()
        parameters.pop("page", None)
        context["pagination_query"] = parameters.urlencode()
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["status_filter"] = self.request.GET.get("status", "")
        context["type_filter"] = self.request.GET.get("type", "")
        context["location_types"] = Location.LocationType.choices
        return context


class LocationDetailView(ProtectedPermissionMixin, DetailView):
    model = Location
    permission_required = "inventory.view_location"
    template_name = "inventory/location_detail.html"
    context_object_name = "location"


class SafeFormMixin:
    success_message = "Ubicación guardada correctamente."

    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            form.add_error(
                None,
                (
                    "No fue posible guardar la ubicación porque sus datos coinciden "
                    "con otra existente."
                ),
            )
            return self.form_invalid(form)
        messages.success(self.request, self.success_message)
        return response


class LocationCreateView(ProtectedPermissionMixin, SafeFormMixin, CreateView):
    model = Location
    form_class = LocationForm
    permission_required = "inventory.add_location"
    template_name = "inventory/location_form.html"
    success_url = reverse_lazy("inventory:location_list")
    success_message = "Ubicación creada correctamente."


class LocationUpdateView(ProtectedPermissionMixin, SafeFormMixin, UpdateView):
    model = Location
    form_class = LocationForm
    permission_required = "inventory.change_location"
    template_name = "inventory/location_form.html"
    success_url = reverse_lazy("inventory:location_list")
    success_message = "Ubicación actualizada correctamente."


class LocationStatusView(ProtectedPermissionMixin, View):
    permission_required = "inventory.change_location_status"

    def post(self, request, pk):
        location = get_object_or_404(Location, pk=pk)
        location.is_active = not location.is_active
        location.save(update_fields=["is_active"])
        messages.success(request, "Estado de la ubicación actualizado correctamente.")
        return redirect("inventory:location_detail", pk=location.pk)


class LocationDeleteView(ProtectedPermissionMixin, DeleteView):
    model = Location
    permission_required = "inventory.delete_location"
    template_name = "inventory/location_confirm_delete.html"
    success_url = reverse_lazy("inventory:location_list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "No se puede eliminar porque la ubicación está siendo utilizada. Desactívela.",
            )
            return redirect(self.success_url)
        messages.success(self.request, "Ubicación eliminada correctamente.")
        return response
