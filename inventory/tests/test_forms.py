import pytest

from inventory.forms import LocationForm
from inventory.models import Location


@pytest.mark.django_db
def test_location_form_exact_fields_bootstrap_autocomplete_valid_and_ignore_status():
    form = LocationForm(
        data={
            "code": "LOC-1",
            "name": "Ubicación",
            "location_type": "BRANCH",
            "address": "Dirección",
            "is_active": False,
        }
    )

    assert list(form.fields) == ["code", "name", "location_type", "address"]
    assert form.fields["code"].widget.attrs["class"] == "form-control"
    assert form.fields["location_type"].widget.attrs["class"] == "form-select"
    assert form.fields["name"].widget.attrs["autocomplete"] == "organization"
    assert form.fields["address"].widget.attrs["autocomplete"] == "street-address"
    assert form.is_valid(), form.errors
    location = form.save()
    assert location.is_active is True


@pytest.mark.django_db
def test_location_form_rejects_blank_invalid_type_and_normalized_duplicate():
    Location.objects.create(code="LOC-1", name="Existente", location_type="BRANCH")
    form = LocationForm(
        data={"code": " loc-1 ", "name": " ", "location_type": "INVALID", "address": ""}
    )

    assert not form.is_valid()
    assert {"code", "name", "location_type"} <= set(form.errors)
    assert "constraint" not in str(form.errors).lower()
