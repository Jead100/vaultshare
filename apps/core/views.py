from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Page, Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.generic import TemplateView, View

from apps.files.forms import FileUploadForm
from apps.files.models import UploadedFile

from .utils.request import is_ajax


class HomeView(TemplateView):
    """
    Public landing page.
    """

    template_name = "core/home.html"


class DashboardView(LoginRequiredMixin, View):
    """
    File upload dashboard for logged-in users.
    Supports AJAX and standard form submissions.
    """

    template_name = "core/dashboard.html"
    list_partial_template = "_partials/_files_list.html"
    PAGE_SIZE = 10

    # --- helpers ---

    def _page(self, request, page_number: Any) -> Page:
        """
        Return a paginated page of the current user's uploaded files.
        Falls back gracefully on invalid or out-of-range page numbers.
        """
        qs = (
            UploadedFile.objects.filter(user=request.user)
            .active()
            .order_by("-uploaded_at", "-id")
        )
        paginator = Paginator(qs, self.PAGE_SIZE)
        return paginator.get_page(page_number)

    def _context(self, request, page: Page, form: FileUploadForm | None = None) -> dict:
        """
        Build the template context for rendering.
        """
        return {
            "form": form or FileUploadForm(user=request.user),
            "files": page.object_list,
            "page_obj": page,
            "paginator": page.paginator,
        }

    def _payload(self, page: Page, html: str) -> dict:
        """
        JSON envelope for successful list renders (used by AJAX).
        """
        return {
            "success": True,
            "html": html,
            "page": page.number,
            "num_pages": page.paginator.num_pages,
            "count": page.paginator.count,
        }

    # --- HTTP methods ---

    def get(self, request):
        page = self._page(request, request.GET.get("page", 1))
        ctx = self._context(request, page)

        if is_ajax(request):
            html = render_to_string(self.list_partial_template, ctx, request)
            return JsonResponse(self._payload(page, html))

        return render(request, self.template_name, ctx)

    def post(self, request):
        form = FileUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()

            if is_ajax(request):
                # Rebuild the first page (newest first) after upload
                first_page = self._page(request, 1)
                ctx = self._context(request, first_page)
                html = render_to_string(self.list_partial_template, ctx, request)
                return JsonResponse(self._payload(first_page, html), status=201)

            return redirect("core:dashboard")

        # Invalid form
        if is_ajax(request):
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

        page = self._page(request, request.GET.get("page", 1))
        ctx = self._context(request, page, form)
        return render(request, self.template_name, ctx, status=400)
