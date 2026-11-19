"""Only the healthcheck is exposed during IDR-001."""
from django.http import JsonResponse
from django.urls import path


def healthcheck(request):
    return JsonResponse({"status": "ok", "service": "identity-reference-poc"})


urlpatterns = [
    path("health/", healthcheck, name="health"),
]
