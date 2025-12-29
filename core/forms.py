from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Hobby, Profile

class SupplierUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the Community Guidelines and Limited Liability terms"
    )
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'terms_accepted')

class HobbyForm(forms.ModelForm):
    category = forms.CharField(
        required=False,
        help_text="Pick an existing category or type a new one.",
        widget=forms.TextInput(attrs={"placeholder": "Category"}),
    )
    tags = forms.CharField(
        required=False,
        help_text="Add tags (existing or new).",
        widget=forms.TextInput(attrs={"placeholder": "Tags"}),
    )
    requirements = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Hobby
        fields = [
            'title','description','image','max_participants',
            'date','place','province','city','neighbourhood',
            'start_datetime','end_datetime','recurrence'
        ]
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows':4}),
        }

class ProfileForm(forms.ModelForm):
    remove_image = forms.BooleanField(required=False)
    remove_image2 = forms.BooleanField(required=False)
    remove_image3 = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        has_existing = bool(
            instance
            and (
                getattr(instance, "image", None)
                or getattr(instance, "image2", None)
                or getattr(instance, "image3", None)
            )
        )
        if not has_existing:
            # Make the primary image field required for users with no pictures yet.
            self.fields["image"].required = True
            self.fields["image"].widget.attrs["required"] = "required"

    class Meta:
        model = Profile
        fields = ['bio', 'goal', 'image', 'image2', 'image3']

    def clean(self):
        cleaned = super().clean()
        instance = getattr(self, "instance", None)

        def keep_or_new(field, remove_field):
            if cleaned.get(remove_field):
                return False
            if self.files.get(field):
                return True
            if instance and getattr(instance, field):
                return True
            return False

        has_any = (
            keep_or_new("image", "remove_image")
            or keep_or_new("image2", "remove_image2")
            or keep_or_new("image3", "remove_image3")
        )
        if not has_any:
            self.add_error("image", "At least one profile picture is required.")
        return cleaned
