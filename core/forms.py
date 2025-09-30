from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Hobby, Profile

class SupplierUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class HobbyForm(forms.ModelForm):
    class Meta:
        model = Hobby
        fields = [
            'title', 'description', 'image', 'max_participants',
            'date', 'place', 'province', 'city', 'neighbourhood'
        ]
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'goal', 'image']