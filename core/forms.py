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
    requirements = forms.CharField(widget=forms.HiddenInput(), required=False)  # added

    class Meta:
        model = Hobby
        fields = ['title', 'description', 'image', 'max_participants', 'date', 'place']  # added image
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
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