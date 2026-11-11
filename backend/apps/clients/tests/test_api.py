import pytest

from apps.accounts.models import Role
from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.clients.tests.factories import ClientFactory
from apps.projects.models import ProjectStatus, Stage
from apps.projects.tests.factories import ProjectFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("role", [Role.ADMIN, Role.PROJECT_MANAGER, Role.DESIGNER, Role.PRODUCTION])
def test_every_staff_role_can_view_clients(login, role):
    client = ClientFactory(company_name="Aurelia Audio Labs", notes="Two approvers.")
    ProjectFactory(client=client)
    ProjectFactory(client=client, stage=Stage.TURNOVER, status=ProjectStatus.COMPLETED)
    ClientFactory(company_name="Zenith Displays")

    body = login(StaffFactory(role=role)).get("/api/clients/").json()

    assert [item["company_name"] for item in body["results"]] == [
        "Aurelia Audio Labs",
        "Zenith Displays",
    ]
    first = body["results"][0]
    assert (first["project_count"], first["active_project_count"]) == (2, 1)
    assert first["notes"] == "Two approvers."


def test_clients_can_be_searched_and_opened(login):
    client = ClientFactory(company_name="Kapetirya Coffee House", contact_person="Nico Ramos")
    ClientFactory(company_name="Lunaria Skin Studio")
    api = login(StaffFactory())

    found = api.get("/api/clients/?q=nico").json()
    detail = api.get(f"/api/clients/{client.pk}/")

    assert [item["company_name"] for item in found["results"]] == ["Kapetirya Coffee House"]
    assert detail.status_code == 200
    assert detail.json()["contact_person"] == "Nico Ramos"


def test_client_users_cannot_list_or_open_client_records(login):
    client_user = UserFactory()
    api = login(client_user)

    assert api.get("/api/clients/").status_code == 403
    # Not even their own record: it carries staff-only notes.
    assert api.get(f"/api/clients/{client_user.client_id}/").status_code == 403
