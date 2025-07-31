from django import forms
from .models import Hobby, Profile, Requirement, Tag, Category
from django.core.exceptions import ValidationError
import uuid

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

    def clean_title(self):
        title = self.cleaned_data['title']
        if Hobby.objects.filter(title=title).exists():
            raise ValidationError("A hobby/event with this name already exists. Please choose a different name.")
        return title

    def save(self, commit=True):
        instance = super().save(commit=False)
        image = self.cleaned_data.get('image', None)
        if image:
            ext = image.name.split('.')[-1]
            image.name = f"hobby_{uuid.uuid4().hex}.{ext}"
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'goal', 'image']