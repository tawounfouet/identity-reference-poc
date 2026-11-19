"""Validate the browser-visible Host before any app endpoint can respond.

Django's ALLOWED_HOSTS is only evaluated when get_host() is accessed. A simple
healthcheck or custom endpoint might otherwise skip that validation.
"""
class ValidateHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.get_host()
        return self.get_response(request)
