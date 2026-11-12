import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.accounts.tests.factories import TEST_PASSWORD, StaffFactory, UserFactory
from apps.activity.models import ActivityAction, ActivityLog

pytestmark = pytest.mark.django_db


@pytest.fixture
def browser():
    """A client that enforces CSRF like a real browser session does."""
    return APIClient(enforce_csrf_checks=True)


def csrf_token(client) -> str:
    response = client.get("/api/auth/csrf/")
    assert response.status_code == 200
    return response.cookies["csrftoken"].value


def sign_in(client, email, password=TEST_PASSWORD):
    token = csrf_token(client)
    return client.post(
        "/api/auth/login/",
        {"email": email, "password": password},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    )


def test_me_requires_a_session_and_sets_the_csrf_cookie(browser):
    response = browser.get("/api/auth/me/")

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
    assert "csrftoken" in response.cookies


def test_session_answers_200_for_visitors_and_for_signed_in_users(browser):
    visitor = browser.get("/api/auth/session/")

    assert visitor.status_code == 200
    assert visitor.json() == {"user": None}
    assert "csrftoken" in visitor.cookies

    user = StaffFactory()
    sign_in(browser, user.email)
    signed_in = browser.get("/api/auth/session/").json()

    assert signed_in["user"]["email"] == user.email
    assert signed_in["user"]["home_path"] == "/app"
    assert signed_in["user"]["permissions"]["view_dashboard"] is True


@pytest.mark.parametrize(
    ("role", "home_path"),
    [
        (Role.ADMIN, "/app"),
        (Role.PROJECT_MANAGER, "/app"),
        (Role.DESIGNER, "/app"),
        (Role.PRODUCTION, "/app"),
        (Role.CLIENT, "/portal"),
    ],
)
def test_sign_in_returns_role_permissions_and_the_right_area(browser, role, home_path):
    user = UserFactory(role=role) if role == Role.CLIENT else StaffFactory(role=role)

    response = sign_in(browser, user.email)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == user.email
    assert body["role"] == role
    assert body["home_path"] == home_path
    assert body["is_company_staff"] is (role != Role.CLIENT)
    assert isinstance(body["permissions"], dict)
    assert body["permissions"]["view_dashboard"] is (role != Role.CLIENT)
    assert body["permissions"]["manage_users"] is (role == Role.ADMIN)

    me = browser.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.json()["id"] == user.id


def test_client_user_sees_their_company_in_me(browser):
    user = UserFactory(client__company_name="Aurelia Audio Labs")

    body = sign_in(browser, user.email).json()

    assert body["client"] == {"id": user.client_id, "company_name": "Aurelia Audio Labs"}
    assert body["role_label"] == "Client"


def test_email_is_not_case_sensitive_at_sign_in(browser):
    user = StaffFactory(email="pm@fabrisee.test")

    response = sign_in(browser, "  PM@FabriSee.test ")

    assert response.status_code == 200
    assert response.json()["id"] == user.id


def test_sign_in_is_recorded_in_the_activity_log(browser):
    user = StaffFactory()

    sign_in(browser, user.email)

    entry = ActivityLog.objects.get()
    assert entry.action == ActivityAction.USER_LOGIN
    assert entry.actor == user
    user.refresh_from_db()
    assert user.last_login is not None


def test_wrong_password_is_rejected_without_saying_which_part_is_wrong(browser):
    user = StaffFactory()

    wrong_password = sign_in(browser, user.email, "not-the-password")
    unknown_email = sign_in(browser, "nobody@example.test", TEST_PASSWORD)

    for response in (wrong_password, unknown_email):
        assert response.status_code == 400
        assert response.json() == {
            "detail": "The email or password is incorrect.",
            "code": "invalid_credentials",
            "fields": {},
        }
    assert browser.get("/api/auth/me/").status_code == 401
    assert not ActivityLog.objects.exists()


def test_inactive_user_cannot_sign_in(browser):
    user = StaffFactory(is_active=False)

    response = sign_in(browser, user.email)

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_credentials"


def test_user_of_an_inactive_client_cannot_sign_in(browser):
    user = UserFactory(client__is_active=False)

    response = sign_in(browser, user.email)

    assert response.status_code == 400
    assert response.json()["code"] == "account_inactive"
    assert browser.get("/api/auth/me/").status_code == 401


def test_missing_fields_are_reported_per_field(browser):
    token = csrf_token(browser)

    response = browser.post("/api/auth/login/", {}, format="json", HTTP_X_CSRFTOKEN=token)

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["fields"] == {
        "email": ["Enter your email address."],
        "password": ["Enter your password."],
    }


def test_sign_in_without_csrf_token_is_refused(browser):
    user = StaffFactory()

    response = browser.post(
        "/api/auth/login/", {"email": user.email, "password": TEST_PASSWORD}, format="json"
    )

    assert response.status_code == 403
    assert response.json()["code"] == "csrf_failed"


def test_unsafe_requests_of_a_signed_in_user_need_the_csrf_token(browser):
    user = StaffFactory()
    sign_in(browser, user.email)

    refused = browser.post("/api/auth/privacy-ack/")
    token = browser.cookies["csrftoken"].value
    accepted = browser.post("/api/auth/privacy-ack/", HTTP_X_CSRFTOKEN=token)

    assert refused.status_code == 403
    assert refused.json()["code"] == "csrf_failed"
    assert accepted.status_code == 200


def test_sign_out_ends_the_session(browser):
    user = StaffFactory()
    sign_in(browser, user.email)
    token = browser.cookies["csrftoken"].value

    response = browser.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=token)

    assert response.status_code == 204
    assert browser.get("/api/auth/me/").status_code == 401


def test_sign_in_attempts_are_limited_per_minute(browser, settings):
    user = StaffFactory()
    token = csrf_token(browser)

    statuses = [
        browser.post(
            "/api/auth/login/",
            {"email": user.email, "password": "wrong"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        ).status_code
        for _ in range(11)
    ]

    assert statuses[:10] == [400] * 10
    assert statuses[10] == 429


def test_privacy_notice_is_acknowledged_once(login):
    user = UserFactory()
    client = login(user)
    assert client.get("/api/auth/me/").json()["privacy_acknowledged_at"] is None

    first = client.post("/api/auth/privacy-ack/")
    acknowledged_at = first.json()["privacy_acknowledged_at"]
    second = client.post("/api/auth/privacy-ack/")

    assert first.status_code == 200
    assert acknowledged_at is not None
    # Acknowledging again keeps the first date.
    assert second.json()["privacy_acknowledged_at"] == acknowledged_at


def test_privacy_acknowledgment_requires_sign_in(api_client):
    assert api_client.post("/api/auth/privacy-ack/").status_code == 401


def test_privacy_notice_text_is_public_and_names_the_company(api_client):
    response = api_client.get("/api/auth/privacy-notice/")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Privacy notice"
    kinds = {block["type"] for block in body["blocks"]}
    assert kinds == {"paragraph", "heading", "list"}
    text = str(body["blocks"])
    assert "Five Brothers Solutions Inc." in text
    assert "{company_name}" not in text
