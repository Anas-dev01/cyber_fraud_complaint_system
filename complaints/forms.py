from django import forms
from .models import Complaint
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Validate every file returned by a multiple-file input."""

    def clean(self, data, initial=None):
        if not data:
            return []

        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleFileField, self).clean(file, initial) for file in files]


class ComplaintForm(forms.ModelForm):
    evidence_files = MultipleFileField(
        required=False,
        label="Upload evidence (screenshots, receipts, or documents)",
        widget=MultipleFileInput(attrs={'multiple': True}),
    )

    class Meta:
        model = Complaint
        fields = ['fraud_type', 'description', 'amount_lost', 'date_of_incident']
        widgets = {
            'date_of_incident': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

class VictimRegistrationForm(UserCreationForm):
    # We explicitly define these to make them required and add styling
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    email = forms.EmailField(max_length=254, help_text='Required for case updates.')
    phone_number = forms.CharField(
        max_length=30,
        required=True,
        label='Phone number',
        help_text='Include your country code where applicable.',
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super(VictimRegistrationForm, self). __init__(*args, **kwargs)
        # Adding Bootstrap classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
