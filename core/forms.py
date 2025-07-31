from django import forms
from .models import Hobby, Profile

class HobbyForm(forms.ModelForm):
    class Meta:
        model = Hobby
        fields = [
            'title', 'description', 'image', 'category', 'tags',
            'max_participants', 'date', 'place'
        ]
        widgets = {
            'tags': forms.CheckboxSelectMultiple,
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'goal', 'image']