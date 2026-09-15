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

from .forms import CategoryForm, ProductForm
from .models import Category, Product


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
    success_message = "Registro eliminado correctamente."
    protected_message = (
        "No se puede eliminar porque el registro está siendo utilizado. Desactívelo."
    )

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.protected_message)
            return redirect(self.success_url)
        messages.success(self.request, self.success_message)
        return response


class CategoryListView(ProtectedPermissionMixin, FilteredListMixin, ListView):
    model = Category
    permission_required = "catalog.view_category"
    template_name = "catalog/category_list.html"
    context_object_name = "categories"
    search_fields = ("name",)


class CategoryDetailView(ProtectedPermissionMixin, DetailView):
    model = Category
    permission_required = "catalog.view_category"
    template_name = "catalog/category_detail.html"
    context_object_name = "category"


class CategoryCreateView(ProtectedPermissionMixin, SafeFormMixin, CreateView):
    model = Category
    form_class = CategoryForm
    permission_required = "catalog.add_category"
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")
    success_message = "Categoría creada correctamente."


class CategoryUpdateView(ProtectedPermissionMixin, SafeFormMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    permission_required = "catalog.change_category"
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")
    success_message = "Categoría actualizada correctamente."


class CategoryStatusView(ProtectedPermissionMixin, View):
    permission_required = "catalog.change_category_status"

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.is_active = not category.is_active
        category.save(update_fields=["is_active"])
        messages.success(request, "Estado de la categoría actualizado correctamente.")
        return redirect("catalog:category_detail", pk=category.pk)


class CategoryDeleteView(ProtectedPermissionMixin, ProtectedDeleteMixin, DeleteView):
    model = Category
    permission_required = "catalog.delete_category"
    template_name = "catalog/category_confirm_delete.html"
    success_url = reverse_lazy("catalog:category_list")
    success_message = "Categoría eliminada correctamente."


class ProductListView(ProtectedPermissionMixin, FilteredListMixin, ListView):
    model = Product
    permission_required = "catalog.view_product"
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    search_fields = ("sku", "barcode", "name")

    def get_queryset(self):
        queryset = super().get_queryset().select_related("category")
        category = self.request.GET.get("category", "")
        if category.isdecimal():
            queryset = queryset.filter(category_id=int(category))
        unit = self.request.GET.get("unit", "")
        if unit in Product.UnitOfMeasure.values:
            queryset = queryset.filter(unit_of_measure=unit)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.order_by("name")
        context["units"] = Product.UnitOfMeasure.choices
        context["category_filter"] = self.request.GET.get("category", "")
        context["unit_filter"] = self.request.GET.get("unit", "")
        return context


class ProductDetailView(ProtectedPermissionMixin, DetailView):
    model = Product
    permission_required = "catalog.view_product"
    template_name = "catalog/product_detail.html"
    context_object_name = "product"
    queryset = Product.objects.select_related("category")


class ProductCreateView(ProtectedPermissionMixin, SafeFormMixin, CreateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.add_product"
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_list")
    success_message = "Producto creado correctamente."


class ProductUpdateView(ProtectedPermissionMixin, SafeFormMixin, UpdateView):
    model = Product
    form_class = ProductForm
    permission_required = "catalog.change_product"
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_list")
    success_message = "Producto actualizado correctamente."


class ProductStatusView(ProtectedPermissionMixin, View):
    permission_required = "catalog.change_product_status"

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.is_active = not product.is_active
        product.save(update_fields=["is_active"])
        messages.success(request, "Estado del producto actualizado correctamente.")
        return redirect("catalog:product_detail", pk=product.pk)


class ProductDeleteView(ProtectedPermissionMixin, ProtectedDeleteMixin, DeleteView):
    model = Product
    permission_required = "catalog.delete_product"
    template_name = "catalog/product_confirm_delete.html"
    success_url = reverse_lazy("catalog:product_list")
    success_message = "Producto eliminado correctamente."
