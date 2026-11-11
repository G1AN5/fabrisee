import factory

from apps.accounts.models import Role, User
from apps.clients.tests.factories import ClientFactory

TEST_PASSWORD = "Correct-Horse-42"


class UserFactory(factory.django.DjangoModelFactory):
    """A client user by default; use the role traits or `StaffFactory` for staff."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n + 1}@example.test")
    full_name = factory.Sequence(lambda n: f"Test User {n + 1}")
    role = Role.CLIENT
    client = factory.Maybe(
        factory.LazyAttribute(lambda o: o.role == Role.CLIENT),
        yes_declaration=factory.SubFactory(ClientFactory),
        no_declaration=None,
    )
    password = factory.django.Password(TEST_PASSWORD)
    is_active = True

    class Params:
        admin = factory.Trait(role=Role.ADMIN, client=None)
        project_manager = factory.Trait(role=Role.PROJECT_MANAGER, client=None)
        designer = factory.Trait(role=Role.DESIGNER, client=None)
        production = factory.Trait(role=Role.PRODUCTION, client=None)


class StaffFactory(UserFactory):
    """A staff member (project manager unless another role is given)."""

    role = Role.PROJECT_MANAGER
    client = None
