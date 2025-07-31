from django import forms
from .models import Hobby, Profile, Requirement, Tag, Category

class HobbyForm(forms.ModelForm):
    new_category = forms.CharField(required=False, label="Add New Category")
    new_tag = forms.CharField(required=False, label="Add New Tag")
    new_requirements = forms.CharField(required=False, label="Add New Requirements (comma separated)")
    requirements = forms.ModelMultipleChoiceField(
        queryset=Requirement.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Requirements"
    )

    class Meta:
        model = Hobby
        exclude = ['host', 'category', 'tags']  # Exclude host, category, tags
        widgets = {
            'tags': forms.CheckboxSelectMultiple,
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'goal', 'image']