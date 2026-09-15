from django import forms

from .models import Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["code", "name", "location_type", "address"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        autocomplete = {"name": "organization", "address": "street-address"}
        for name, field in self.fields.items():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class
            field.widget.attrs["autocomplete"] = autocomplete.get(name, "off")

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        duplicate = Location.objects.filter(code__iexact=code).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("Ya existe una ubicación con este código.")
        return code
