from project_configuration.urls import DJANGO_ADMIN_BASE_URL


class DisableCSRFMiddleware:
    """Due the SessionAuthentication performs its own CSRF validation,
    to avoid get the CSRF missing error even when the CSRF Middleware is disable and
    session authentication is enable, we add this middleware
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if DJANGO_ADMIN_BASE_URL not in request.path:
            setattr(request, '_dont_enforce_csrf_checks', True)
        response = self.get_response(request)
        return response
