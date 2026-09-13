from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class RegistrationForm(UserCreationForm):
    """
    Registration form extending Django's built-in UserCreationForm
    (which already handles password hashing and validation) with
    email and role fields.
    """
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Profile.Role.choices, initial=Profile.Role.CUSTOMER)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            css_class = 'form-select' if name == 'role' else 'form-control'
            field.widget.attrs['class'] = f"{existing} {css_class}".strip()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile = user.profile
            profile.role = self.cleaned_data['role']
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.save()
        return user


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing} form-control".strip()


class ProfileUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'department']


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
