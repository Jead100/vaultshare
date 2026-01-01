from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AuthTailwindFormMixin:
    """
    Mixin to apply Tailwind styles to public auth forms, skipping
    hidden + file fields.
    """

    base = (
        "w-full px-4 py-3 border border-gray-300 rounded-xl "
        "focus:outline-none focus:ring-2 focus:ring-blue-400 "
        "focus:border-transparent bg-gray-50 text-gray-900 transition duration-200"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for bf in self.visible_fields():
            w = bf.field.widget
            if getattr(w, "input_type", None) in {"hidden", "file"}:
                continue
            existing = w.attrs.get("class", "")
            w.attrs["class"] = f"{existing} {self.base}".strip()
            # Set placeholders for text, email, or password
            if getattr(w, "input_type", "") in {"text", "email", "password"}:
                w.attrs.setdefault("placeholder", bf.label)


class PasswordConfirmMixin(forms.Form):
    """
    Add password1/password2, confirm they match, and hash on save.
    """

    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("The two password fields didn’t match."))
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# Public auth forms


class SignUpForm(AuthTailwindFormMixin, PasswordConfirmMixin, forms.ModelForm):
    """
    Public registration form using email + name + password confirmation.
    """

    class Meta:
        model = User
        fields = (
            "email",
            "name",
        )
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "placeholder": _("Email"),
                    "autocomplete": "email",
                    "autofocus": True,
                }
            ),
            "name": forms.TextInput(
                attrs={"placeholder": _("Name"), "autocomplete": "name"}
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("An account with this email already exists."))
        return email


class EmailLoginForm(AuthTailwindFormMixin, AuthenticationForm):
    """
    Login form that displays email for the username field.
    """

    username = forms.EmailField(label=_("Email"))


# Admin forms


class AdminUserCreationForm(PasswordConfirmMixin, forms.ModelForm):
    """
    Admin: create users with repeated password.
    """

    class Meta:
        model = User
        fields = ("email", "name")


class AdminUserChangeForm(forms.ModelForm):
    """
    Admin: update users; show password hash as read-only.
    """

    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this user’s "
            "password, but you can change the password using "
            '<a href="../password/">this form</a>.'
        ),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "name",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    def clean_password(self):
        # Preserve the existing (hashed) password regardless of input.
        return self.initial.get("password")
