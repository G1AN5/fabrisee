import pytest
from django.core import mail

from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.notifications.models import EmailLog, EmailStatus, Notification, NotificationEvent
from apps.notifications.services import deliver_email, email_subject, notify
from apps.projects.tests.factories import ProjectFactory

pytestmark = pytest.mark.django_db

DATABASE_BACKEND = "apps.notifications.backends.DatabaseEmailBackend"


@pytest.fixture
def database_email_backend(settings):
    """Django's test runner swaps in the in-memory backend; use the development one."""
    settings.EMAIL_BACKEND = DATABASE_BACKEND


def test_notify_creates_one_notification_and_one_logged_email_per_recipient():
    project = ProjectFactory(project_number="FS-2026-0007", title="Trade fair booth")
    approver = UserFactory(client=project.client, full_name="Joanna Cruz")

    created = notify(
        event=NotificationEvent.REVISION_UPLOADED,
        recipients=[approver, project.manager],
        title="Design R2 is waiting for your approval",
        message="Please review the new design revision.",
        project=project,
        section="design",
    )

    assert len(created) == 2
    for_approver = Notification.objects.get(user=approver)
    assert for_approver.event == NotificationEvent.REVISION_UPLOADED
    assert for_approver.is_read is False
    # Each side gets a deep link to its own area.
    assert for_approver.link == f"/portal/projects/{project.pk}/designs"
    assert Notification.objects.get(user=project.manager).link == (
        f"/app/projects/{project.pk}/revisions"
    )

    email = EmailLog.objects.get(to=approver.email)
    assert email.subject == "[FabriSee] FS-2026-0007 · Design R2 is waiting for your approval"
    assert email.status == EmailStatus.LOGGED
    assert email.notification == for_approver
    assert "Hello Joanna Cruz," in email.body_text
    assert f"http://localhost:5173/portal/projects/{project.pk}/designs" in email.body_text
    assert "Five Brothers Solutions Inc." in email.body_text


def test_notify_never_notifies_the_person_who_caused_the_event():
    project = ProjectFactory()
    designer = StaffFactory()

    notify(
        event=NotificationEvent.REVISION_UPLOADED,
        recipients=[designer, project.manager],
        title="Design R1 uploaded",
        project=project,
        actor=designer,
    )

    assert not Notification.objects.filter(user=designer).exists()
    assert Notification.objects.filter(user=project.manager).count() == 1


def test_notify_skips_duplicates_inactive_users_and_missing_recipients():
    project = ProjectFactory()
    inactive = UserFactory(client=project.client, is_active=False)

    created = notify(
        event=NotificationEvent.STAGE_CHANGED,
        recipients=[project.manager, project.manager, None, inactive],
        title="The project moved to Production",
        project=project,
    )

    assert [n.user for n in created] == [project.manager]
    assert EmailLog.objects.count() == 1


def test_notification_without_project_has_no_link():
    user = StaffFactory()

    notify(event=NotificationEvent.REQUEST_SUBMITTED, recipients=[user], title="Welcome")

    notification = Notification.objects.get()
    assert notification.link == ""
    assert email_subject("Welcome") == "[FabriSee] Welcome"


def test_database_backend_keeps_emails_in_the_log_without_duplicates(database_email_backend):
    user = StaffFactory()
    notify(event=NotificationEvent.STAGE_CHANGED, recipients=[user], title="Stage changed")
    log = EmailLog.objects.get()

    deliver_email(log.pk)

    log.refresh_from_db()
    assert EmailLog.objects.count() == 1
    assert log.status == EmailStatus.LOGGED


def test_mail_sent_outside_notify_is_logged_by_the_database_backend(database_email_backend):
    mail.send_mail("Password reset", "Use this link.", None, ["someone@example.test"])

    log = EmailLog.objects.get()
    assert log.to == "someone@example.test"
    assert log.subject == "Password reset"


def test_real_backend_marks_the_email_as_sent(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    user = StaffFactory()
    notify(event=NotificationEvent.STAGE_CHANGED, recipients=[user], title="Stage changed")
    log = EmailLog.objects.get()

    deliver_email(log.pk)

    log.refresh_from_db()
    assert log.status == EmailStatus.SENT
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]


def test_failed_delivery_is_recorded_and_does_not_raise(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    settings.EMAIL_HOST = "127.0.0.1"
    settings.EMAIL_PORT = 1  # nothing listens here
    user = StaffFactory()
    notify(event=NotificationEvent.STAGE_CHANGED, recipients=[user], title="Stage changed")
    log = EmailLog.objects.get()

    deliver_email(log.pk)

    log.refresh_from_db()
    assert log.status == EmailStatus.FAILED
    assert log.error
