import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import Role, User
from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.clients.tests.factories import ClientFactory

pytestmark = pytest.mark.django_db


def test_email_is_the_login_and_is_stored_in_lower_case():
    user = User.objects.create_user(
        email="  Joanna@Aurelia.TEST ",
        password="Correct-Horse-42",
        full_name="Joanna Cruz",
        role=Role.CLIENT,
        client=ClientFactory(),
    )

    assert user.email == "joanna@aurelia.test"
    assert User.USERNAME_FIELD == "email"
    assert user.check_password("Correct-Horse-42")
    assert User.objects.get_by_natural_key("JOANNA@aurelia.test") == user


def test_email_must_be_unique():
    UserFactory(email="same@example.test")

    with pytest.raises(IntegrityError), transaction.atomic():
        UserFactory(email="same@example.test")


def test_client_user_must_belong_to_a_client():
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            email="orphan@example.test", password="x", full_name="No Client", role=Role.CLIENT
        )


@pytest.mark.parametrize("role", [Role.ADMIN, Role.PROJECT_MANAGER, Role.DESIGNER, Role.PRODUCTION])
def test_staff_member_must_not_belong_to_a_client(role):
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(
            email="staff@example.test",
            password="x",
            full_name="Staff Member",
            role=role,
            client=ClientFactory(),
        )


def test_clean_explains_the_client_rule():
    user = User(email="a@example.test", full_name="A B", role=Role.CLIENT)

    with pytest.raises(ValidationError) as error:
        user.clean()

    assert "client" in error.value.message_dict


def test_superuser_is_an_administrator_with_admin_site_access():
    user = User.objects.create_superuser(
        email="root@example.test", password="x", full_name="Root User"
    )

    assert user.role == Role.ADMIN
    assert user.is_staff
    assert user.is_superuser
    assert user.client is None


def test_role_helpers_and_home_path():
    client_user = UserFactory()
    manager = StaffFactory()

    assert client_user.is_client_user
    assert not client_user.is_company_staff
    assert client_user.home_path == "/portal"
    assert manager.is_company_staff
    assert not manager.is_client_user
    assert manager.home_path == "/app"


def test_short_name_and_initials():
    user = StaffFactory(full_name="Andrea Villanueva")

    assert user.short_name == "A. Villanueva"
    assert user.initials == "AV"
    assert StaffFactory(full_name="Cher").initials == "CH"
    assert StaffFactory(full_name="Maria Clara Delos Reyes").initials == "MR"
