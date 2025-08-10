from django import forms
from .models import Hobby, Profile

class HobbyForm(forms.ModelForm):
    category = forms.CharField(
        required=False,
        help_text="Enter a category for your hobby."
    )
    tags = forms.CharField(
        required=False,
        help_text="Enter tags separated by commas."
    )

    class Meta:
        model = Hobby
        fields = ['title', 'description', 'max_participants', 'date', 'place']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'goal', 'image']