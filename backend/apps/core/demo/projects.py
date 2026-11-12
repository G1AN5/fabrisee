"""The eight demo projects, one for each situation the system must show (guide section 12).

Dates are relative to the moment the data is loaded, so the dashboard always shows pending
and overdue items. Everything here is fictitious.
"""

from datetime import timedelta

from apps.core.choices import DecisionChannel
from apps.projects.models import DocumentType, ProjectType, Stage

from . import drawing, pdfs
from .scenario import DemoBuilder, ProjectStory


def _reference_image(scene: str, title: str, subtitle: str, *, sketch: bool, **options) -> bytes:
    return drawing.render_image(
        scene,
        title=title,
        subtitle=subtitle,
        label="Reference",
        kind="Client reference sketch" if sketch else "Client reference photo",
        sketch=sketch,
        **options,
    )


def window_display_refresh(b: DemoBuilder) -> None:
    """5. Aurelia Audio Labs: Turnover (completed), with turnover documents."""
    story = ProjectStory(
        b,
        client_key="aurelia",
        title="Window display refresh",
        project_type=ProjectType.STORE_INTERIOR,
        location="Aurelia Audio Labs concept store, Level 2, Amihan Square, Mandaluyong City",
        dimensions="Window bay 3.2 m wide × 2.6 m high × 0.9 m deep",
        description=(
            "Refresh of the storefront window for the holiday season: a raised platform, "
            "three product pedestals, and a backlit brand panel."
        ),
        target_date=b.date_in(-12),
        manager_key="pm",
        scene="window_display",
    )
    story.submit(
        "joanna",
        b.on(50, "10:12"),
        references=[
            (
                "current-window.png",
                _reference_image(
                    "window_display",
                    "Current window display",
                    "Aurelia Audio Labs",
                    sketch=False,
                    variant=0,
                ),
            )
        ],
    )
    story.designate("pm", b.on(50, "13:40"), ["joanna", "mark"])
    story.quote(
        "pm",
        b.on(48, "15:05"),
        [
            ("Platform and three pedestals (MDF, laminate finish)", 1, 78000),
            ("Backlit brand panel", 1, 62500),
            ("Installation after mall hours", 1, 28000),
            ("Delivery and site protection", 1, 18000),
        ],
        notes="Installation is scheduled after mall hours, as the mall requires.",
    )
    story.accept_quotation("joanna", b.on(47, "09:48"))
    story.upload_revision(
        "designer",
        b.on(43, "16:20"),
        notes="Three pedestals at different heights and a warm backlit panel.",
        materials=[
            ("Platform", "MDF, oak laminate", "3.1 m × 0.8 m × 0.15 m"),
            ("Pedestals (3)", "MDF, matte white paint", "0.45 m × 0.45 m, three heights"),
            ("Brand panel", "Acrylic face, warm white LED backlight", "1.5 m × 0.8 m"),
        ],
        variant=1,
    )
    story.approve("joanna", b.on(42, "11:02"), comment="Looks great. Approved.")
    story.approve("mark", b.on(41, "14:36"))
    story.change_stage(
        "production",
        b.on(18, "17:10"),
        Stage.DELIVERY_INSTALLATION,
        "Fabrication is complete. Installation is scheduled for two nights after mall hours.",
    )
    turned_over = b.on(14, "09:25")
    story.change_stage(
        "production",
        turned_over,
        Stage.TURNOVER,
        "Installed and inspected with the client. The turnover checklist is signed.",
    )
    project = story.project
    story.add_document(
        "production",
        turned_over + timedelta(minutes=20),
        doc_type=DocumentType.TURNOVER,
        name="turnover-checklist.pdf",
        content=pdfs.turnover_pdf(
            company=b.company,
            project_number=project.project_number,
            project_title=project.title,
            client_name=story.client.company_name,
            location=project.location,
            turned_over_on=story._local_date(turned_over),
            turned_over_by="Ramon Dizon",
            received_by="Joanna Cruz",
            checklist=[
                "Platform and pedestals installed, level, and secured",
                "Backlit brand panel tested with the store lighting",
                "Finishes checked: no scratches or gaps",
                "Site cleaned and protective covers removed",
                "Care instructions explained to the store staff",
            ],
        ),
        visible=True,
    )
    story.add_document(
        "production",
        turned_over + timedelta(minutes=26),
        doc_type=DocumentType.TURNOVER,
        name="installed-window-display.png",
        content=drawing.render_image(
            "window_display",
            title="Installed window display",
            subtitle=story._subtitle(),
            label="Installed",
            kind="FabriSee demo photo",
            variant=1,
        ),
        visible=True,
    )
    story.add_document(
        "pm",
        turned_over + timedelta(hours=2),
        doc_type=DocumentType.OTHER,
        name="site-access-notes.pdf",
        content=pdfs.brief_pdf(
            company=b.company,
            title="Site access notes",
            reference=project.project_number,
            paragraphs=[
                "Internal note for the installation team. Not shared with the client.",
                "Loading bay access is through the basement. The mall allows work between "
                "10 PM and 6 AM only, with a work permit filed two days ahead.",
            ],
        ),
        visible=False,
    )
    story.finish()


def cafe_counter(b: DemoBuilder) -> None:
    """3. Kapetirya Coffee House: Production; R3 approved and locked; R1, R2 in history."""
    story = ProjectStory(
        b,
        client_key="kapetirya",
        title="Café counter and menu signage",
        project_type=ProjectType.STORE_INTERIOR,
        location="Kapetirya Coffee House, Ground Floor, Dalisay Arcade, Marikina City",
        dimensions="Counter 3.6 m long × 0.75 m deep × 1.05 m high; menu board 2.4 m × 0.9 m",
        description=(
            "New service counter with a pastry display and a wall-mounted menu board for "
            "the second branch."
        ),
        target_date=b.date_in(-2),
        manager_key="pm",
        scene="cafe_counter",
    )
    materials = [
        ("Counter body", "Plywood carcass, wood laminate", "3.6 m × 0.75 m"),
        ("Counter top", "Solid surface, off-white", "3.7 m × 0.8 m"),
        ("Menu board", "Powder-coated steel frame, changeable panels", "2.4 m × 0.9 m"),
    ]
    story.submit("nico", b.on(45, "08:55"))
    story.designate("pm", b.on(45, "10:30"), ["nico"])
    story.quote(
        "pm",
        b.on(43, "14:20"),
        [
            ("Service counter with solid surface top", 1, 185000),
            ("Pastry display case integration", 1, 48000),
            ("Menu board with changeable panels", 1, 54000),
            ("Lighting and electrical rough-in", 1, 27000),
            ("Delivery and installation", 1, 28000),
        ],
    )
    story.accept_quotation("nico", b.on(41, "19:12"))
    story.upload_revision(
        "designer",
        b.on(37, "15:45"),
        notes="First layout: dark walnut counter, menu board on the side wall.",
        materials=materials,
        variant=1,
    )
    story.request_changes(
        "nico",
        b.on(35, "20:05"),
        "The counter is too tall for our baristas. Please lower it to 1.05 m and move the "
        "menu board to the back wall so customers can read it from the queue.",
    )
    story.upload_revision(
        "designer",
        b.on(30, "11:30"),
        notes="Counter lowered to 1.05 m; menu board moved to the back wall.",
        materials=materials,
        variant=2,
    )
    story.request_changes(
        "nico",
        b.on(27, "18:40"),
        "Much better. The wood tone is too dark for the space, though. Please use light "
        "oak and add closed storage under the counter.",
    )
    uploaded = b.on(9, "09:10")
    story.upload_revision(
        "designer",
        uploaded,
        notes="Light oak finish, closed storage under the counter, pastry display case added.",
        materials=[
            ("Counter body", "Plywood carcass, light oak laminate, four storage doors", "3.6 m"),
            ("Counter top", "Solid surface, off-white", "3.7 m × 0.8 m"),
            ("Pastry display case", "Tempered glass, LED strip", "1.0 m × 0.5 m × 0.4 m"),
            ("Menu board", "Powder-coated steel frame, changeable panels", "2.4 m × 0.9 m"),
        ],
        variant=3,
    )
    story.remind(uploaded + b.reminder_threshold)
    story.approve(
        "nico",
        b.on(5, "14:05"),
        comment="Approved. Thank you for the changes.",
        recorder_key="pm",
        channel=DecisionChannel.PHONE,
    )
    story.finish()


def trade_fair_booth(b: DemoBuilder) -> None:
    """4. Lunaria Skin Studio: Delivery and Installation."""
    story = ProjectStory(
        b,
        client_key="lunaria",
        title="Trade fair booth, 3 m × 6 m",
        project_type=ProjectType.EVENT_BOOTH,
        location="Hall B, Silangan Convention Center, Pasay City",
        dimensions="3 m × 6 m booth; 2.4 m wall height; raised floor 0.1 m",
        description=(
            "Booth for a three-day beauty trade fair: back wall with a brand panel, product "
            "shelves, a consultation counter, and storage."
        ),
        target_date=b.date_in(2),
        manager_key="pm",
        scene="fair_booth",
    )
    materials = [
        ("Walls", "Modular panels, white laminate", "6.0 m × 2.4 m back, 3.0 m side"),
        ("Brand panel", "Printed acrylic, LED edge light", "2.5 m × 1.25 m"),
        ("Counter", "MDF, plum laminate, cream top", "1.8 m × 0.6 m × 1.0 m"),
        ("Floor", "Raised platform, carpet tiles", "3 m × 6 m"),
    ]
    story.submit("bianca", b.on(38, "13:15"))
    story.designate("pm", b.on(38, "15:00"), ["bianca"])
    story.quote(
        "pm",
        b.on(36, "10:40"),
        [
            ("Booth structure and wall panels", 1, 168000),
            ("Raised flooring and carpet", 1, 46000),
            ("Product shelves and consultation counter", 1, 92000),
            ("Graphics and lighting", 1, 74000),
            ("Delivery, installation, and dismantling", 1, 48000),
        ],
        notes="The price includes dismantling after the fair.",
    )
    story.accept_quotation("bianca", b.on(34, "16:22"))
    story.upload_revision(
        "designer",
        b.on(30, "17:05"),
        notes="First layout with a brand panel on the back wall and a counter at the side.",
        materials=materials,
        variant=1,
    )
    story.request_changes(
        "bianca",
        b.on(29, "10:18"),
        "Please add product shelves on the left wall and make the brand panel larger. "
        "The counter should face the aisle.",
    )
    story.upload_revision(
        "designer",
        b.on(26, "14:50"),
        notes="Larger brand panel, shelves on the left wall, counter facing the aisle.",
        materials=[*materials, ("Shelves (3)", "MDF, cream paint", "1.4 m × 0.25 m each")],
        variant=2,
    )
    story.approve("bianca", b.on(25, "09:33"), comment="This is what we wanted. Approved.")
    story.change_stage(
        "production",
        b.on(2, "08:35"),
        Stage.DELIVERY_INSTALLATION,
        "Booth modules are loaded for delivery. Installation at the venue starts tomorrow morning.",
    )
    story.finish()


def experience_counter(b: DemoBuilder) -> None:
    """1. Aurelia Audio Labs: Design; R2 pending; Joanna approved, Mark pending for 3 days."""
    story = ProjectStory(
        b,
        client_key="aurelia",
        title="Experience counter and brand wall",
        project_type=ProjectType.STORE_INTERIOR,
        location="Aurelia Audio Labs flagship store, Level 1, Habagat Center, Makati City",
        dimensions="Brand wall 4.8 m wide × 2.7 m high; experience counter 3.0 m long × 0.8 m deep",
        description=(
            "Listening counter with demo stations and a backlit brand wall for the new "
            "flagship store."
        ),
        target_date=b.date_in(35),
        manager_key="pm",
        scene="experience_counter",
    )
    story.submit(
        "joanna",
        b.on(21, "11:20"),
        references=[
            (
                "counter-idea-sketch.png",
                _reference_image(
                    "experience_counter",
                    "Counter idea",
                    "Aurelia Audio Labs",
                    sketch=True,
                    variant=1,
                ),
            )
        ],
    )
    story.designate("pm", b.on(21, "14:05"), ["joanna", "mark"])
    story.quote(
        "pm",
        b.on(19, "16:30"),
        [
            ("Brand wall with backlit panel", 1, 248000),
            ("Experience counter with listening stations", 1, 196000),
            ("Integrated lighting and cable management", 1, 84000),
            ("Delivery and installation", 1, 84000),
        ],
        notes="Installation after mall hours; two nights on site.",
    )
    story.accept_quotation("mark", b.on(17, "10:44"))
    story.upload_revision(
        "designer",
        b.on(12, "15:15"),
        notes="Brand wall with cool white backlight and two listening stations.",
        materials=[
            ("Brand wall", "MDF panel, matte teal laminate, cool white LED backlight", "4.8 m"),
            ("Counter body", "Plywood carcass, oak veneer", "3.0 m × 0.8 m × 0.95 m"),
            ("Listening stations (2)", "Powder-coated steel stands", "0.3 m high"),
        ],
        variant=1,
    )
    story.approve("joanna", b.on(11, "09:50"), comment="Looks good to me.")
    story.request_changes(
        "mark",
        b.on(10, "17:28"),
        "The brand wall lighting should be warm white, not cool. Please add two more "
        "listening stations; two are not enough for weekends.",
    )
    uploaded = b.at_least(3, "10:20")
    story.upload_revision(
        "designer",
        uploaded,
        notes="Warm white lighting on the brand wall; listening stations increased to four.",
        materials=[
            ("Brand wall", "MDF panel, matte teal laminate, warm white LED backlight", "4.8 m"),
            ("Counter body", "Plywood carcass, oak veneer", "3.0 m × 0.8 m × 0.95 m"),
            ("Listening stations (4)", "Powder-coated steel stands", "0.3 m high"),
        ],
        variant=2,
    )
    story.approve(
        "joanna", uploaded + timedelta(hours=4, minutes=35), comment="Warm white is right."
    )
    story.remind(uploaded + b.reminder_threshold)
    story.finish()


def popup_booth(b: DemoBuilder) -> None:
    """7. Kapetirya Coffee House: Design; R1 changes requested; R2 not yet uploaded."""
    story = ProjectStory(
        b,
        client_key="kapetirya",
        title="Pop-up booth for weekend market",
        project_type=ProjectType.EVENT_BOOTH,
        location="Weekend market at the town plaza, Marikina City",
        dimensions="2 m × 2 m footprint; counter 1.8 m long; canopy height 2.3 m",
        description=(
            "Foldable pop-up coffee booth that fits in a van: counter, back shelf, and "
            "overhead signage."
        ),
        target_date=b.date_in(6),
        manager_key="pm",
        scene="popup_booth",
    )
    story.submit("nico", b.on(12, "07:40"))
    story.designate("pm", b.on(12, "09:15"), ["nico"])
    story.quote(
        "pm",
        b.on(11, "13:10"),
        [
            ("Foldable counter and frame", 1, 52000),
            ("Canopy and signage", 1, 24500),
            ("Shelving and storage crates", 1, 12000),
            ("Delivery", 1, 8000),
        ],
    )
    story.accept_quotation("nico", b.on(10, "08:22"))
    story.upload_revision(
        "designer",
        b.on(5, "16:55"),
        notes="Canopy with striped awning, slatted counter, and a back shelf for cups.",
        materials=[
            ("Frame", "Aluminum tube, powder coated", "2.0 m × 2.0 m × 2.3 m"),
            ("Counter", "Marine plywood slats, sealed", "1.8 m × 0.6 m × 1.0 m"),
            ("Canopy", "Canvas, green and cream stripes", "2.2 m × 2.2 m"),
        ],
        variant=1,
    )
    story.request_changes(
        "nico",
        b.on(2, "17:45"),
        "Please make the counter foldable in two parts so it fits in our van, add a shelf "
        "for the grinder, and make the sign readable from the side.",
    )
    story.finish()


def endcap_display(b: DemoBuilder) -> None:
    """8. Lunaria Skin Studio: Request; quotation v1 returned with comments; v2 in draft."""
    story = ProjectStory(
        b,
        client_key="lunaria",
        title="End-cap product display",
        project_type=ProjectType.DISPLAY_STAND,
        location="Partner beauty stores (four branches), Metro Manila",
        dimensions="0.9 m wide × 0.45 m deep × 1.6 m high per unit",
        description="End-cap display units for a new serum line, with a header and three shelves.",
        target_date=b.date_in(40),
        manager_key="owner",
        scene="endcap_display",
        designer_key=None,
    )
    story.submit(
        "bianca",
        b.on(9, "10:05"),
        references=[
            (
                "endcap-sketch.png",
                _reference_image(
                    "endcap_display", "End-cap idea", "Lunaria Skin Studio", sketch=True
                ),
            )
        ],
    )
    story.designate("owner", b.on(9, "11:30"), ["bianca"])
    story.quote(
        "owner",
        b.on(7, "15:40"),
        [
            ("End-cap display unit", 6, 21500),
            ("Lit header panel", 6, 3000),
            ("Delivery to four branches", 1, 11000),
        ],
    )
    story.return_quotation(
        "bianca",
        b.on(4, "15:12"),
        "The total is above our budget for this launch. Please requote for four units "
        "instead of six and use a printed header without lighting.",
    )
    story.quote(
        "owner",
        b.hours_ago(26),
        [
            ("End-cap display unit", 4, 21500),
            ("Printed header panel", 4, 3000),
            ("Delivery to four branches", 1, 14000),
        ],
        notes="Requote for four units with a printed header, as requested.",
        send=False,
    )
    story.finish()


def display_stands(b: DemoBuilder) -> None:
    """2. Tindahan Tech PH: Request; quotation v1 sent 3 days ago, no decision."""
    story = ProjectStory(
        b,
        client_key="tindahan",
        title="Product display stands (set of 6)",
        project_type=ProjectType.DISPLAY_STAND,
        location="Tindahan Tech PH partner stores, Quezon City and Caloocan City",
        dimensions="0.6 m wide × 0.45 m deep × 1.7 m high per stand",
        description=(
            "Six freestanding stands for phone accessories, each with hooks, two shelves, "
            "and a header sign."
        ),
        target_date=b.date_in(45),
        manager_key="pm",
        scene="display_stands",
        designer_key=None,
    )
    story.submit(
        "liza",
        b.on(6, "11:05"),
        references=[
            (
                "stand-sketch.png",
                _reference_image("display_stands", "Stand idea", "Tindahan Tech PH", sketch=True),
            )
        ],
    )
    story.designate("pm", b.on(6, "13:20"), ["liza"])
    sent = b.at_least(3, "09:40")
    story.quote(
        "pm",
        sent,
        [
            ("Freestanding display stand", 6, 38500),
            ("Header sign with print", 6, 4500),
            ("Delivery to two cities", 1, 17000),
        ],
    )
    story.remind(sent + b.reminder_threshold)
    story.finish()


def illuminated_sign(b: DemoBuilder) -> None:
    """6. Tindahan Tech PH: Request; new, no quotation yet."""
    story = ProjectStory(
        b,
        client_key="tindahan",
        title="Illuminated brand sign",
        project_type=ProjectType.BRAND_SIGN,
        location="Tindahan Tech PH main branch, Quezon City",
        dimensions="Sign face 4.0 m wide × 0.9 m high; letter height 0.5 m",
        description=(
            "Front-lit channel letter sign for the storefront, replacing the old tarpaulin banner."
        ),
        target_date=b.date_in(60),
        manager_key="pm",
        scene="storefront_sign",
        designer_key=None,
    )
    story.submit(
        "liza",
        b.hours_ago(20),
        references=[
            (
                "storefront-photo.png",
                _reference_image(
                    "storefront_sign", "Storefront today", "Tindahan Tech PH", sketch=False
                ),
            ),
            (
                "sign-layout-brief.pdf",
                pdfs.brief_pdf(
                    company="Tindahan Tech PH",
                    title="Sign layout brief",
                    reference="Main branch storefront",
                    paragraphs=[
                        "We would like front-lit channel letters with our name in one line.",
                        "Letter height about 0.5 m. The sign should be readable from across "
                        "the road at night.",
                        "The landlord allows a sign face of up to 4.0 m by 0.9 m.",
                    ],
                    from_client=True,
                ),
            ),
        ],
    )
    story.finish()


# In the order the projects were created, which is the order of their project numbers.
STORIES = [
    window_display_refresh,
    cafe_counter,
    trade_fair_booth,
    experience_counter,
    popup_booth,
    endcap_display,
    display_stands,
    illuminated_sign,
]
