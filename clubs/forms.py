from django import forms
from django.forms import ClearableFileInput

from .models import Club, PASTEL_COLORS


class ClubForm(forms.ModelForm):
    color = forms.ChoiceField(
        required=False,
        choices=[('', 'Random pastel (default)')] + [(color, color) for color in PASTEL_COLORS],
        widget=forms.RadioSelect(attrs={
            'class': 'hidden'  # Hide default widget, we render manually in template
        }),
        help_text='Pick a pastel color for the club card or leave blank for random.'
    )
    logo = forms.ImageField(
        required=False,
        widget=ClearableFileInput(attrs={
            'class': 'input',
            'accept': 'image/*'
        }),
        help_text='Upload a square logo for best results (optional).'
    )

    def __init__(self, *args, **kwargs):
        disable_name = kwargs.pop('disable_name', False)
        super().__init__(*args, **kwargs)
        if disable_name:
            self.fields['name'].disabled = True
        self.fields['color'].widget.attrs.setdefault('aria-label', 'Club color palette')
        # Ensure color field is initialized with instance value if available
        if self.instance and self.instance.pk:
            self.fields['color'].initial = self.instance.color

    def clean_color(self):
        color = self.cleaned_data.get('color')
        return color or ''

    class Meta:
        model = Club
        fields = ['name', 'description', 'logo', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Enter club name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'input',
                'rows': 5,
                'placeholder': 'Describe your club - what is it about? Who should join?'
            }),
        }
        help_texts = {
            'name': 'Choose a unique, memorable name for your club.',
            'description': 'Tell potential members what your club is all about.',
        }

