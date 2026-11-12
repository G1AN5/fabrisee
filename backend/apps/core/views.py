from django.conf import settings
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config import VERSION


class HealthView(APIView):
    """`GET /api/health/`: tells the frontend, CI and monitoring that the API is up."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        database = "ok"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            database = "unavailable"
        healthy = database == "ok"
        return Response(
            {
                "status": "ok" if healthy else "degraded",
                "service": "fabrisee",
                "version": VERSION,
                "database": database,
                "time": timezone.localtime().isoformat(timespec="seconds"),
                "time_zone": settings.TIME_ZONE,
            },
            status=200 if healthy else 503,
        )


class DemoAccountsView(APIView):
    """`GET /api/demo/accounts/`: the demo accounts, for the sign-in page.

    Exists only in development while the demo data is loaded (`DEBUG` and
    `ALLOW_DEMO_SEED`). Everywhere else it answers 404, like an unknown path.
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.accounts.models import User
        from apps.core.demo.accounts import DEMO_PASSWORD, USERS

        if not (settings.DEBUG and settings.ALLOW_DEMO_SEED):
            raise NotFound("This API endpoint does not exist.")
        existing = {
            user.email: user
            for user in User.objects.filter(
                email__in=[account.email for account in USERS], is_active=True
            ).select_related("client")
        }
        if not existing:
            raise NotFound("This API endpoint does not exist.")
        accounts = [
            {
                "email": account.email,
                "full_name": account.full_name,
                "role": account.role,
                "role_label": existing[account.email].get_role_display(),
                "company": (
                    existing[account.email].client.company_name
                    if existing[account.email].client_id
                    else None
                ),
                "note": account.note,
            }
            for account in USERS
            if account.email in existing
        ]
        return Response({"password": DEMO_PASSWORD, "accounts": accounts})


def api_not_found(request, *args, **kwargs):
    """Unknown `/api/...` paths answer in the API error format, not with the React app."""
    return JsonResponse(
        {"detail": "This API endpoint does not exist.", "code": "not_found", "fields": {}},
        status=404,
    )


DEV_NOTE = """<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>FabriSee API</title></head>
  <body style="font-family: system-ui, sans-serif; margin: 3rem; color: #0F172A;">
    <h1 style="font-size: 1.25rem;">FabriSee API server</h1>
    <p>This port serves the API and the Django admin. Open the app at
      <a href="{frontend_url}">{frontend_url}</a>.</p>
    <p>API health: <a href="/api/health/">/api/health/</a> · Django admin:
      <a href="/admin/">/admin/</a></p>
  </body>
</html>
"""


@ensure_csrf_cookie
def spa_index(request, *args, **kwargs):
    """Serve the built React app for every non-API path (production).

    In development the Vite dev server serves the app, so this view only shows a short
    note that points to it.
    """
    index_file = settings.FRONTEND_DIST_DIR / "index.html"
    if index_file.is_file():
        response = HttpResponse(index_file.read_bytes(), content_type="text/html; charset=utf-8")
        response["Cache-Control"] = "no-cache"
        return response
    if settings.DEBUG:
        return HttpResponse(DEV_NOTE.format(frontend_url=settings.FRONTEND_URL))
    return HttpResponse(
        "The FabriSee frontend has not been built. Run `npm run build` in frontend/.",
        content_type="text/plain; charset=utf-8",
        status=503,
    )
