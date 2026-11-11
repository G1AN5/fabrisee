from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.activity.models import ActivityAction
from apps.activity.services import log_activity
from apps.core.models import SystemSetting

from .authentication import SessionAuthentication
from .privacy import load_privacy_notice
from .serializers import CurrentUserSerializer, LoginSerializer


class InvalidCredentials(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "invalid_credentials"
    default_detail = "The email or password is incorrect."


class AccountInactive(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "account_inactive"
    default_detail = (
        "This account is no longer active. Contact the company if you think this is a mistake."
    )


class LoginRateThrottle(AnonRateThrottle):
    """Limits sign-in attempts per IP address (rate `login` in the settings)."""

    scope = "login"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """`GET /api/auth/csrf/`: set the `csrftoken` cookie before the first unsafe request."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"detail": "CSRF cookie set."})


class LoginView(APIView):
    """`POST /api/auth/login/`: start a session with email and password."""

    # No session authentication here: the request is anonymous. CSRF is still enforced
    # below so that another site cannot sign a visitor in to an account of its choice.
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        SessionAuthentication().enforce_csrf(request)
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request._request,
            username=serializer.validated_data["email"].strip().lower(),
            password=serializer.validated_data["password"],
        )
        if user is None:
            raise InvalidCredentials()
        if user.is_client_user and not user.client.is_active:
            raise AccountInactive()

        login(request._request, user)
        log_activity(action=ActivityAction.USER_LOGIN, actor=user)
        return Response(CurrentUserSerializer(user).data)


class LogoutView(APIView):
    """`POST /api/auth/logout/`: end the session."""

    permission_classes = [AllowAny]

    def post(self, request):
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MeView(APIView):
    """`GET /api/auth/me/`: the signed-in user with role and permissions (401 if none)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class PrivacyNoticeView(APIView):
    """`GET /api/auth/privacy-notice/`: the wording of the privacy notice."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(load_privacy_notice(SystemSetting.load().company_name))


class PrivacyAcknowledgeView(APIView):
    """`POST /api/auth/privacy-ack/`: record that the user read the privacy notice."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.privacy_acknowledged_at is None:
            user.privacy_acknowledged_at = timezone.now()
            user.save(update_fields=["privacy_acknowledged_at", "updated_at"])
        return Response(CurrentUserSerializer(user).data)
