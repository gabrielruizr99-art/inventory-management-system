from django.db import migrations


MODEL_PERMISSIONS = {
    ("catalog", "category"): {
        "add_category": "Can add category",
        "change_category": "Can change category",
        "change_category_status": "Can change category status",
        "delete_category": "Can delete category",
        "view_category": "Can view category",
    },
    ("catalog", "product"): {
        "add_product": "Can add product",
        "change_product": "Can change product",
        "change_product_status": "Can change product status",
        "delete_product": "Can delete product",
        "view_product": "Can view product",
    },
    ("partners", "supplier"): {
        "add_supplier": "Can add supplier",
        "change_supplier": "Can change supplier",
        "change_supplier_status": "Can change supplier status",
        "delete_supplier": "Can delete supplier",
        "view_supplier": "Can view supplier",
    },
    ("partners", "customer"): {
        "add_customer": "Can add customer",
        "change_customer": "Can change customer",
        "change_customer_status": "Can change customer status",
        "delete_customer": "Can delete customer",
        "view_customer": "Can view customer",
    },
    ("inventory", "location"): {
        "add_location": "Can add location",
        "change_location": "Can change location",
        "change_location_status": "Can change location status",
        "delete_location": "Can delete location",
        "view_location": "Can view location",
    },
}

GROUP_PERMISSIONS = {
    "Administrador": {
        permission_codename
        for permissions in MODEL_PERMISSIONS.values()
        for permission_codename in permissions
    },
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


def _phase2_permissions(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    database_alias = schema_editor.connection.alias
    permissions_by_codename = {}

    for (app_label, model), permission_names in MODEL_PERMISSIONS.items():
        content_type, _ = ContentType.objects.using(database_alias).get_or_create(
            app_label=app_label,
            model=model,
        )
        for codename, name in permission_names.items():
            permission, _ = Permission.objects.using(database_alias).get_or_create(
                content_type_id=content_type.pk,
                codename=codename,
                defaults={"name": name},
            )
            permissions_by_codename[codename] = permission

    return permissions_by_codename


def assign_phase2_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    permissions_by_codename = _phase2_permissions(apps, schema_editor)
    database_alias = schema_editor.connection.alias
    group_permission = Group._meta.get_field("permissions").remote_field.through

    for group_name, codenames in GROUP_PERMISSIONS.items():
        group = Group.objects.using(database_alias).get(name=group_name)
        for codename in codenames:
            group_permission.objects.using(database_alias).get_or_create(
                group_id=group.pk,
                permission_id=permissions_by_codename[codename].pk,
            )


def unassign_phase2_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    permissions_by_codename = _phase2_permissions(apps, schema_editor)
    database_alias = schema_editor.connection.alias
    group_permission = Group._meta.get_field("permissions").remote_field.through

    for group_name, codenames in GROUP_PERMISSIONS.items():
        group = Group.objects.using(database_alias).filter(name=group_name).first()
        if group is None:
            continue
        permission_ids = [permissions_by_codename[codename].pk for codename in codenames]
        group_permission.objects.using(database_alias).filter(
            group_id=group.pk,
            permission_id__in=permission_ids,
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_create_initial_groups"),
        ("catalog", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("inventory", "0001_initial"),
        ("partners", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(assign_phase2_permissions, unassign_phase2_permissions),
    ]
