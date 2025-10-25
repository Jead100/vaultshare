from django.http import HttpRequest

def is_ajax(request: HttpRequest) -> bool:
    """
    Return True if the request was made via JS (AJAX/fetch).
    """
    return request.headers.get("x-requested-with") == "XMLHttpRequest"
