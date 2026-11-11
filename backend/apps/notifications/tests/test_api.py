import pytest

from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.notifications.models import NotificationEvent
from apps.notifications.tests.factories import NotificationFactory
from apps.projects.tests.factories import ProjectFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return StaffFactory()


def test_list_returns_only_the_users_notifications_with_the_unread_count(login, user):
    project = ProjectFactory(project_number="FS-2026-0007", title="Trade fair booth")
    NotificationFactory(user=user, title="Older", is_read=True)
    NotificationFactory(
        user=user,
        title="Design R2 is waiting",
        project=project,
        event=NotificationEvent.REVISION_UPLOADED,
        link=f"/app/projects/{project.pk}/revisions",
    )
    NotificationFactory(title="Somebody else's")

    body = login(user).get("/api/notifications/").json()

    assert body["count"] == 2
    assert body["unread_count"] == 1
    newest = body["results"][0]
    assert newest["title"] == "Design R2 is waiting"
    assert newest["event_label"] == "Design revision uploaded"
    assert newest["link"] == f"/app/projects/{project.pk}/revisions"
    assert newest["project"] == {
        "id": project.pk,
        "project_number": "FS-2026-0007",
        "title": "Trade fair booth",
    }
    assert newest["is_read"] is False


def test_list_filters_by_unread_and_event(login, user):
    NotificationFactory(user=user, title="Read", is_read=True)
    NotificationFactory(
        user=user, title="Unread reminder", event=NotificationEvent.DECISION_REMINDER
    )
    api = login(user)

    unread = api.get("/api/notifications/?unread=1").json()
    reminders = api.get("/api/notifications/?event=decision_reminder").json()
    read = api.get("/api/notifications/?unread=0").json()

    assert [n["title"] for n in unread["results"]] == ["Unread reminder"]
    assert [n["title"] for n in reminders["results"]] == ["Unread reminder"]
    assert [n["title"] for n in read["results"]] == ["Read"]
    # The unread count is always the total, whatever the filter.
    assert read["unread_count"] == 1


def test_mark_one_notification_as_read(login, user):
    notification = NotificationFactory(user=user)
    NotificationFactory(user=user)

    response = login(user).post(f"/api/notifications/{notification.pk}/read/")

    assert response.status_code == 200
    assert response.json()["notification"]["is_read"] is True
    assert response.json()["unread_count"] == 1
    notification.refresh_from_db()
    assert notification.read_at is not None

    # Marking it again keeps the first time.
    first_read_at = notification.read_at
    login(user).post(f"/api/notifications/{notification.pk}/read/")
    notification.refresh_from_db()
    assert notification.read_at == first_read_at


def test_a_user_cannot_mark_somebody_elses_notification(login, user):
    other = NotificationFactory()

    response = login(user).post(f"/api/notifications/{other.pk}/read/")

    assert response.status_code == 404
    other.refresh_from_db()
    assert other.is_read is False


def test_mark_all_as_read_only_touches_the_users_own(login, user):
    NotificationFactory.create_batch(3, user=user)
    other = NotificationFactory()

    response = login(user).post("/api/notifications/read-all/")

    assert response.json() == {"marked": 3, "unread_count": 0}
    assert login(user).get("/api/notifications/").json()["unread_count"] == 0
    other.refresh_from_db()
    assert other.is_read is False


def test_client_users_have_their_own_notifications_too(login):
    client_user = UserFactory()
    NotificationFactory(user=client_user, title="Quotation v1 is waiting for your decision")

    body = login(client_user).get("/api/notifications/").json()

    assert body["unread_count"] == 1
    assert body["results"][0]["title"] == "Quotation v1 is waiting for your decision"
