from importlib import import_module
from types import SimpleNamespace

import pytest
from django.apps import apps as django_apps
from django.contrib.auth.models import Group, Permission
from django.db import connection

MODEL_ACTIONS = {
    "catalog.category": {
        "add_category",
        "change_category",
        "change_category_status",
        "delete_category",
        "view_category",
    },
    "catalog.product": {
        "add_product",
        "change_product",
        "change_product_status",
        "delete_product",
        "view_product",
    },
    "partners.supplier": {
        "add_supplier",
        "change_supplier",
        "change_supplier_status",
        "delete_supplier",
        "view_supplier",
    },
    "partners.customer": {
        "add_customer",
        "change_customer",
        "change_customer_status",
        "delete_customer",
        "view_customer",
    },
    "inventory.location": {
        "add_location",
        "change_location",
        "change_location_status",
        "delete_location",
        "view_location",
    },
}

EXPECTED_BY_GROUP = {
    "Administrador": set().union(*MODEL_ACTIONS.values()),
    "Vendedor": {
        "view_category",
        "view_product",
        "add_customer",
        "change_customer",
        "view_customer",
        "view_location",
    },
    "Almacén": {
        "add_category",
        "change_category",
        "change_category_status",
        "view_category",
        "add_product",
        "change_product",
        "change_product_status",
        "view_product",
        "add_supplier",
        "change_supplier",
        "change_supplier_status",
        "view_supplier",
        "view_location",
    },
}


@pytest.mark.django_db
def test_phase2_default_and_custom_permissions_exist():
    for model_key, expected_codenames in MODEL_ACTIONS.items():
        app_label, model = model_key.split(".")
        actual_codenames = set(
            Permission.objects.filter(
                content_type__app_label=app_label,
                content_type__model=model,
            ).values_list("codename", flat=True)
        )
        assert actual_codenames == expected_codenames


@pytest.mark.django_db
def test_phase2_group_permission_matrix_is_exact():
    phase2_app_labels = {"catalog", "partners", "inventory"}

    assert set(Group.objects.values_list("name", flat=True)) >= set(EXPECTED_BY_GROUP)
    for group_name, expected_codenames in EXPECTED_BY_GROUP.items():
        group = Group.objects.get(name=group_name)
        actual_codenames = set(
            group.permissions.filter(content_type__app_label__in=phase2_app_labels).values_list(
                "codename", flat=True
            )
        )
        assert actual_codenames == expected_codenames


@pytest.mark.django_db
def test_phase2_permission_migration_is_idempotent():
    permission_migration = import_module("accounts.migrations.0003_assign_phase2_permissions")
    schema_editor = SimpleNamespace(connection=connection)

    permission_migration.assign_phase2_permissions(django_apps, schema_editor)
    permission_migration.assign_phase2_permissions(django_apps, schema_editor)

    test_phase2_group_permission_matrix_is_exact()


@pytest.mark.django_db
def test_reverse_permission_migration_removes_only_phase2_assignments():
    permission_migration = import_module("accounts.migrations.0003_assign_phase2_permissions")
    schema_editor = SimpleNamespace(connection=connection)
    administrator = Group.objects.get(name="Administrador")
    unrelated_permission = Permission.objects.get(
        content_type__app_label="auth",
        codename="view_group",
    )
    administrator.permissions.add(unrelated_permission)

    permission_migration.unassign_phase2_permissions(django_apps, schema_editor)

    assert Group.objects.filter(name__in=EXPECTED_BY_GROUP).count() == 3
    assert administrator.permissions.filter(pk=unrelated_permission.pk).exists()
    assert not administrator.permissions.filter(
        content_type__app_label__in={"catalog", "partners", "inventory"}
    ).exists()
