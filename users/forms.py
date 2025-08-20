from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import User


class AuthTailwindFormMixin:
    """
    Mixin to apply Tailwind styles to auth forms (login/signup), 
    skipping hidden + file fields.
    """
    base = ("w-full px-4 py-3 border border-gray-300 rounded-xl "
            "focus:outline-none focus:ring-2 focus:ring-blue-400 "
            "focus:border-transparent bg-gray-50 text-gray-900 transition duration-200")

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


class CustomUserCreationForm(AuthTailwindFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "password1", "password2"]


class CustomAuthenticationForm(AuthTailwindFormMixin, AuthenticationForm):
    pass
