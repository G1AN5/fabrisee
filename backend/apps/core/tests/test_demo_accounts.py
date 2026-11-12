import pytest

from apps.accounts.models import Role
from apps.accounts.tests.factories import StaffFactory, UserFactory

pytestmark = pytest.mark.django_db

PATH = "/api/demo/accounts/"


@pytest.fixture
def demo_users():
    StaffFactory(email="owner@fabrisee.test", full_name="Teresa Lim", role=Role.ADMIN)
    UserFactory(
        email="joanna@aurelia.test",
        full_name="Joanna Cruz",
        client__company_name="Aurelia Audio Labs",
    )


def test_demo_accounts_are_listed_in_development_with_demo_data(api_client, settings, demo_users):
    settings.DEBUG = True
    settings.ALLOW_DEMO_SEED = True

    response = api_client.get(PATH)

    assert response.status_code == 200
    body = response.json()
    assert body["password"] == "FabriSee@2026"
    assert [account["email"] for account in body["accounts"]] == [
        "owner@fabrisee.test",
        "joanna@aurelia.test",
    ]
    assert body["accounts"][0]["role_label"] == "Administrator"
    assert body["accounts"][1]["company"] == "Aurelia Audio Labs"


@pytest.mark.parametrize(("debug", "allow_seed"), [(False, True), (True, False), (False, False)])
def test_demo_accounts_do_not_exist_outside_development(
    api_client, settings, demo_users, debug, allow_seed
):
    settings.DEBUG = debug
    settings.ALLOW_DEMO_SEED = allow_seed

    response = api_client.get(PATH)

    assert response.status_code == 404
    assert "password" not in response.json()


def test_demo_accounts_do_not_exist_without_demo_data(api_client, settings):
    settings.DEBUG = True
    settings.ALLOW_DEMO_SEED = True
    StaffFactory(email="real.person@example.test")

    assert api_client.get(PATH).status_code == 404
