"""Healthcheck and official django-allauth browser/headless routes."""
from django.http import JsonResponse
from django.urls import include, path


def healthcheck(request):
    return JsonResponse({"status": "ok", "service": "identity-reference-poc"})


urlpatterns = [
    path("health/", healthcheck, name="health"),
    # Headless-only suppresses account HTML login views while preserving the
    # optional provider callback paths for later OAuth tickets.
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
]
