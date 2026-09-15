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

from .forms import CustomerForm, SupplierForm
from .models import Customer, Supplier


class ProtectedPermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name()
            )
        raise PermissionDenied


class FilteredListMixin:
    paginate_by = 20
    search_fields = ()

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            search = Q()
            for field in self.search_fields:
                search |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(search)
        status = self.request.GET.get("status", "")
        if status in {"active", "inactive"}:
            queryset = queryset.filter(is_active=status == "active")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parameters = self.request.GET.copy()
        parameters.pop("page", None)
        context["pagination_query"] = parameters.urlencode()
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["status_filter"] = self.request.GET.get("status", "")
        return context


class SafeFormMixin:
    success_message = "Registro guardado correctamente."

    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            form.add_error(
                None,
                "No fue posible guardar el registro porque sus datos coinciden con otro existente.",
            )
            return self.form_invalid(form)
        messages.success(self.request, self.success_message)
        return response


class ProtectedDeleteMixin:
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "No se puede eliminar porque el registro está siendo utilizado. Desactívelo.",
            )
            return redirect(self.success_url)
        messages.success(self.request, self.success_message)
        return response


class SupplierListView(ProtectedPermissionMixin, FilteredListMixin, ListView):
    model = Supplier
    permission_required = "partners.view_supplier"
    template_name = "partners/supplier_list.html"
    context_object_name = "suppliers"
    search_fields = ("name", "tax_id", "contact_name")


class SupplierDetailView(ProtectedPermissionMixin, DetailView):
    model = Supplier
    permission_required = "partners.view_supplier"
    template_name = "partners/supplier_detail.html"
    context_object_name = "supplier"


class SupplierCreateView(ProtectedPermissionMixin, SafeFormMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    permission_required = "partners.add_supplier"
    template_name = "partners/supplier_form.html"
    success_url = reverse_lazy("partners:supplier_list")
    success_message = "Proveedor creado correctamente."


class SupplierUpdateView(ProtectedPermissionMixin, SafeFormMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    permission_required = "partners.change_supplier"
    template_name = "partners/supplier_form.html"
    success_url = reverse_lazy("partners:supplier_list")
    success_message = "Proveedor actualizado correctamente."


class SupplierStatusView(ProtectedPermissionMixin, View):
    permission_required = "partners.change_supplier_status"

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        supplier.is_active = not supplier.is_active
        supplier.save(update_fields=["is_active"])
        messages.success(request, "Estado del proveedor actualizado correctamente.")
        return redirect("partners:supplier_detail", pk=supplier.pk)


class SupplierDeleteView(ProtectedPermissionMixin, ProtectedDeleteMixin, DeleteView):
    model = Supplier
    permission_required = "partners.delete_supplier"
    template_name = "partners/supplier_confirm_delete.html"
    success_url = reverse_lazy("partners:supplier_list")
    success_message = "Proveedor eliminado correctamente."


class CustomerListView(ProtectedPermissionMixin, FilteredListMixin, ListView):
    model = Customer
    permission_required = "partners.view_customer"
    template_name = "partners/customer_list.html"
    context_object_name = "customers"
    search_fields = ("name", "document_number", "email", "phone")


class CustomerDetailView(ProtectedPermissionMixin, DetailView):
    model = Customer
    permission_required = "partners.view_customer"
    template_name = "partners/customer_detail.html"
    context_object_name = "customer"


class CustomerCreateView(ProtectedPermissionMixin, SafeFormMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    permission_required = "partners.add_customer"
    template_name = "partners/customer_form.html"
    success_url = reverse_lazy("partners:customer_list")
    success_message = "Cliente creado correctamente."


class CustomerUpdateView(ProtectedPermissionMixin, SafeFormMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    permission_required = "partners.change_customer"
    template_name = "partners/customer_form.html"
    success_url = reverse_lazy("partners:customer_list")
    success_message = "Cliente actualizado correctamente."


class CustomerStatusView(ProtectedPermissionMixin, View):
    permission_required = "partners.change_customer_status"

    def post(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        customer.is_active = not customer.is_active
        customer.save(update_fields=["is_active"])
        messages.success(request, "Estado del cliente actualizado correctamente.")
        return redirect("partners:customer_detail", pk=customer.pk)


class CustomerDeleteView(ProtectedPermissionMixin, ProtectedDeleteMixin, DeleteView):
    model = Customer
    permission_required = "partners.delete_customer"
    template_name = "partners/customer_confirm_delete.html"
    success_url = reverse_lazy("partners:customer_list")
    success_message = "Cliente eliminado correctamente."
