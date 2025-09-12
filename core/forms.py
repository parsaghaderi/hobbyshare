from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Hobby, Profile, Supplier

class HobbyForm(forms.ModelForm):
    class Meta:
        model = Hobby
        fields = ['title', 'description', 'image', 'category', 'tags', 'max_participants', 'date', 'recurrence', 'place', 'province', 'city', 'neighbourhood']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'recurrence': forms.Select(attrs={'class': 'form-select'}),
            'place': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'neighbourhood': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProfileForm(forms.ModelForm):
    remove_image = forms.BooleanField(required=False, label='Remove current picture')

    class Meta:
        model = Profile
        fields = ['bio', 'goal', 'image']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell others about yourself'}),
            'goal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'What are you looking to do?'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'image': 'Profile picture',
        }

class SupplierUserCreationForm(UserCreationForm):
    is_supplier = forms.BooleanField(required=False, label='Register as a Supplier?')
    province = forms.CharField(required=False)
    city = forms.CharField(required=False)
    neighbourhood = forms.CharField(required=False, label='Neighbourhood')

    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('is_supplier'):
            for f in ['province','city','neighbourhood']:
                if not cleaned.get(f):
                    self.add_error(f, 'Required for suppliers')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit)
        if self.cleaned_data.get('is_supplier') and commit:
            Supplier.objects.create(
                user=user,
                province=self.cleaned_data.get('province',''),
                city=self.cleaned_data.get('city',''),
                neighbourhood=self.cleaned_data.get('neighbourhood','')
            )
        return user