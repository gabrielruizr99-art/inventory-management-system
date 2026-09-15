import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from inventory.admin import LocationAdmin
from inventory.models import Location


@pytest.mark.django_db
def test_location_creation_defaults_normalization_and_string():
    location = Location.objects.create(
        code="  alm-01  ",
        name="  Almacén central  ",
        location_type=Location.LocationType.WAREHOUSE,
        address="  Dirección de prueba  ",
    )

    assert location.code == "ALM-01"
    assert location.name == "Almacén central"
    assert location.address == "Dirección de prueba"
    assert location.is_active is True
    assert str(location) == "ALM-01 — Almacén central"


@pytest.mark.django_db
def test_location_default_ordering():
    Location.objects.create(code="Z-1", name="Zeta", location_type="WAREHOUSE")
    Location.objects.create(code="A-2", name="Alfa", location_type="BRANCH")
    Location.objects.create(code="A-1", name="Alfa", location_type="BRANCH")

    assert list(Location.objects.values_list("code", flat=True)) == ["A-1", "A-2", "Z-1"]


@pytest.mark.django_db
@pytest.mark.parametrize("location_type", Location.LocationType.values)
def test_location_accepts_each_valid_type(location_type):
    location = Location(code=f"LOC-{location_type}", name="Ubicación", location_type=location_type)

    location.full_clean()
    location.save()

    assert location.location_type == location_type


@pytest.mark.django_db
def test_location_model_validation_rejects_blank_fields_and_invalid_type():
    location = Location(code=" ", name=" ", location_type="INVALID")

    with pytest.raises(ValidationError) as error:
        location.full_clean()

    assert {"code", "name", "location_type"} <= set(error.value.message_dict)


@pytest.mark.django_db
def test_location_database_constraints_reject_blank_and_invalid_values():
    invalid_locations = [
        Location(code=" ", name="Válida", location_type="BRANCH"),
        Location(code="VALID", name=" ", location_type="BRANCH"),
        Location(code="VALID", name="Válida", location_type="INVALID"),
    ]

    for location in invalid_locations:
        with pytest.raises(IntegrityError), transaction.atomic():
            Location.objects.bulk_create([location])


@pytest.mark.django_db
def test_location_code_database_uniqueness_is_normalized():
    Location.objects.create(code="LOC-01", name="Primera", location_type="BRANCH")

    with pytest.raises(IntegrityError), transaction.atomic():
        Location.objects.bulk_create(
            [Location(code=" loc-01 ", name="Segunda", location_type="WAREHOUSE")]
        )


def test_location_constraints_index_and_admin_registration():
    constraint_names = {constraint.name for constraint in Location._meta.constraints}

    assert "inventory_location_code_ci_uniq" in constraint_names
    assert "inventory_location_type_valid" in constraint_names
    assert [index.name for index in Location._meta.indexes] == ["inv_location_type_active_idx"]
    assert isinstance(admin.site._registry[Location], LocationAdmin)
