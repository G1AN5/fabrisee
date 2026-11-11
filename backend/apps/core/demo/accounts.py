"""The demo accounts and client companies (build guide, section 12). All fictitious."""

from dataclasses import dataclass

from apps.accounts.models import Role

# Demo only. Printed by seed_demo and listed in the README.
DEMO_PASSWORD = "FabriSee@2026"
OWNER_EMAIL = "owner@fabrisee.test"


@dataclass(frozen=True)
class DemoClient:
    key: str
    company_name: str
    contact_person: str
    email: str
    phone: str
    address: str
    notes: str  # staff only


@dataclass(frozen=True)
class DemoUser:
    key: str
    email: str
    full_name: str
    role: str
    job_title: str
    phone: str
    client_key: str | None = None
    note: str = ""
    # Whether the privacy notice of the first sign-in is already acknowledged.
    privacy_acknowledged: bool = True
    # Access to the Django admin site.
    is_superuser: bool = False


CLIENTS = [
    DemoClient(
        key="aurelia",
        company_name="Aurelia Audio Labs",
        contact_person="Joanna Cruz",
        email="hello@aurelia.test",
        phone="+63 2 8555 0141",
        address="8th Floor, Lakambini Building, Pasig City",
        notes="Two approvers decide on designs. Store work is allowed only after mall hours.",
    ),
    DemoClient(
        key="tindahan",
        company_name="Tindahan Tech PH",
        contact_person="Liza Mendoza",
        email="trade@tindahantech.test",
        phone="+63 2 8555 0162",
        address="Unit 12, Maharlika Business Park, Quezon City",
        notes="Prefers updates by email. Deliveries go to partner stores, not the head office.",
    ),
    DemoClient(
        key="kapetirya",
        company_name="Kapetirya Coffee House",
        contact_person="Nico Ramos",
        email="kumusta@kapetirya.test",
        phone="+63 917 555 0118",
        address="Ground Floor, Dalisay Arcade, Marikina City",
        notes="The owner decides. He is easiest to reach by phone in the afternoon.",
    ),
    DemoClient(
        key="lunaria",
        company_name="Lunaria Skin Studio",
        contact_person="Bianca Flores",
        email="brand@lunaria.test",
        phone="+63 2 8555 0127",
        address="5th Floor, Amihan Square, Makati City",
        notes="The brand manager approves. The marketing associate follows the projects.",
    ),
]

USERS = [
    DemoUser(
        key="owner",
        email=OWNER_EMAIL,
        full_name="Teresa Lim",
        role=Role.ADMIN,
        job_title="Owner",
        phone="+63 917 555 0101",
        note="Owner",
        is_superuser=True,
    ),
    DemoUser(
        key="pm",
        email="pm@fabrisee.test",
        full_name="Andrea Villanueva",
        role=Role.PROJECT_MANAGER,
        job_title="Account and Project Manager",
        phone="+63 917 555 0102",
        note="Manager of most projects",
    ),
    DemoUser(
        key="designer",
        email="designer@fabrisee.test",
        full_name="Paolo Garcia",
        role=Role.DESIGNER,
        job_title="Designer",
        phone="+63 917 555 0103",
    ),
    DemoUser(
        key="production",
        email="production@fabrisee.test",
        full_name="Ramon Dizon",
        role=Role.PRODUCTION,
        job_title="Production Lead",
        phone="+63 917 555 0104",
        note="Production lead",
    ),
    DemoUser(
        key="joanna",
        email="joanna@aurelia.test",
        full_name="Joanna Cruz",
        role=Role.CLIENT,
        job_title="Marketing Manager",
        phone="+63 917 555 0111",
        client_key="aurelia",
        note="Designated approver",
    ),
    DemoUser(
        key="mark",
        email="mark@aurelia.test",
        full_name="Mark Bautista",
        role=Role.CLIENT,
        job_title="Retail Operations Head",
        phone="+63 917 555 0112",
        client_key="aurelia",
        note="Designated approver",
    ),
    DemoUser(
        key="liza",
        email="liza@tindahantech.test",
        full_name="Liza Mendoza",
        role=Role.CLIENT,
        job_title="Trade Marketing Lead",
        phone="+63 917 555 0113",
        client_key="tindahan",
        note="Designated approver",
    ),
    DemoUser(
        key="nico",
        email="nico@kapetirya.test",
        full_name="Nico Ramos",
        role=Role.CLIENT,
        job_title="Owner",
        phone="+63 917 555 0118",
        client_key="kapetirya",
        note="Designated approver",
    ),
    DemoUser(
        key="bianca",
        email="bianca@lunaria.test",
        full_name="Bianca Flores",
        role=Role.CLIENT,
        job_title="Brand Manager",
        phone="+63 917 555 0115",
        client_key="lunaria",
        note="Designated approver",
    ),
    DemoUser(
        key="ella",
        email="ella@lunaria.test",
        full_name="Ella Navarro",
        role=Role.CLIENT,
        job_title="Marketing Associate",
        phone="+63 917 555 0116",
        client_key="lunaria",
        note="Views only; sees the privacy notice at first sign-in",
        privacy_acknowledged=False,
    ),
]
