from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import User


class BaseStyledForm:
    """Mixin to apply Tailwind styles to all visible fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs.update({
                "class": (
                    "w-full px-4 py-3 border border-gray-300 rounded-xl "
                    "focus:outline-none focus:ring-2 focus:ring-blue-400 "
                    "focus:border-transparent bg-gray-50 text-gray-900 "
                    "transition duration-200"
                )
            })


class CustomUserCreationForm(BaseStyledForm, UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "password1", "password2"]


class CustomAuthenticationForm(BaseStyledForm, AuthenticationForm):
    pass
