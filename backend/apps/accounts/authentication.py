from rest_framework import authentication, exceptions


class SessionAuthentication(authentication.SessionAuthentication):
    """Django session authentication with two API-friendly adjustments.

    * Unauthenticated requests get **401** (not DRF's default 403), so the React app can
      tell "please sign in" from "you may not do this".
    * CSRF failures use the code ``csrf_failed``.
    """

    def authenticate_header(self, request):
        return "Session"

    def enforce_csrf(self, request):
        try:
            super().enforce_csrf(request)
        except exceptions.PermissionDenied as exc:
            raise exceptions.PermissionDenied(
                "Your session could not be verified. Reload the page and try again.",
                code="csrf_failed",
            ) from exc
