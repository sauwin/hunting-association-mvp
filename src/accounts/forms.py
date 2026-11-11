from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="First name")
    last_name = forms.CharField(max_length=150, required=True, label="Last name")
    email = forms.EmailField(required=True, label="Email address")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.role = User.Role.MEMBER
        if commit:
            user.save()
        return user


class EmailOrUsernameLoginForm(forms.Form):
    identifier = forms.CharField(
        label="Email or Username",
        max_length=254,
        widget=forms.TextInput(attrs={"autofocus": True}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        identifier = cleaned_data.get("identifier", "").strip()
        password = cleaned_data.get("password")

        if identifier and password:
            username = identifier
            if "@" in identifier:
                matched_user = User.objects.filter(email__iexact=identifier).first()
                if matched_user:
                    username = matched_user.username

            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid email/username or password. Please try again."
                )
            if not self.user_cache.is_active:
                raise forms.ValidationError("This account is currently inactive.")

        return cleaned_data

    def get_user(self):
        return self.user_cache