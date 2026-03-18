from django import forms

from .models import AssistantCard


class AssistantCardForm(forms.ModelForm):
    class Meta:
        model = AssistantCard
        fields = ["name", "description", "prompt", "agent_type", "is_favorite"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "prompt": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "agent_type": forms.Select(attrs={"class": "form-control"}),
            "is_favorite": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
