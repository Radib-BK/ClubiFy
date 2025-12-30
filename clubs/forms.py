from django import forms
from .models import Club


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'description']
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

