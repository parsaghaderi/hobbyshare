from django import forms
from .models import Hobby, Profile, Requirement

class HobbyForm(forms.ModelForm):
    new_category = forms.CharField(required=False, label="Add New Category")
    new_tags = forms.CharField(required=False, label="Add New Tags (comma separated)")
    new_requirements = forms.CharField(required=False, label="Add New Requirements (comma separated)")
    requirements = forms.ModelMultipleChoiceField(
        queryset=Requirement.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Requirements"
    )

    class Meta:
        model = Hobby
        fields = [
            'title', 'description', 'image', 'category', 'tags',
            'max_participants', 'date', 'place', 'requirements'
        ]
        widgets = {
            'tags': forms.CheckboxSelectMultiple,
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'goal', 'image']