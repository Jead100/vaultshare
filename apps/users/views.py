from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import SignUpForm


class SignUpView(CreateView):
    """
    User registration view
    """

    form_class = SignUpForm
    template_name = "users/registration/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request, "Your account was created successfully. You can log in now."
        )
        return super().form_valid(form)
