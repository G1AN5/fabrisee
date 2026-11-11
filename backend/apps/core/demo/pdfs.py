"""Sample PDF documents for the demo data, generated with fpdf2.

Quotations, design spec sheets, and turnover documents with realistic layouts. Every page
says "Sample document" in the footer. The built-in PDF fonts cover Latin-1 only, so the
peso sign is written as "PHP".
"""

from datetime import date, timedelta
from decimal import Decimal

from fpdf import FPDF
from fpdf.enums import XPos, YPos

INK = (15, 23, 42)
MUTED = (100, 116, 139)
BLUE = (30, 64, 175)
ORANGE = (194, 65, 12)
LINE = (203, 213, 225)

_REPLACEMENTS = {
    "₱": "PHP ",
    "–": "-",
    "—": "-",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "…": "...",
}


def latin1(text: str) -> str:
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def money(amount: Decimal) -> str:
    return f"{amount:,.2f}"


def long_date(value: date) -> str:
    return f"{value:%b} {value.day}, {value.year}"


class SamplePDF(FPDF):
    """An A4 page with the company header and the "Sample document" footer."""

    def __init__(
        self,
        *,
        company: str,
        document_title: str,
        reference: str,
        tagline: str = "Custom fabrication · Parañaque City",
        show_mark: bool = True,
    ):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.tagline = latin1(tagline)
        self.show_mark = show_mark
        self.company = latin1(company)
        self.document_title = latin1(document_title)
        self.reference = latin1(reference)
        self.set_margins(18, 16, 18)
        self.set_auto_page_break(auto=True, margin=20)
        self.set_title(f"{self.document_title} {self.reference}")
        self.set_author(self.company)
        self.set_creator("FabriSee demo data")
        self.add_page()

    def header(self):
        if self.show_mark:
            # The FabriSee mark: a square with one cut corner (drawn, not an image).
            self.set_fill_color(*ORANGE)
            self.polygon([(18, 16), (23.2, 16), (25.5, 18.3), (25.5, 23.5), (18, 23.5)], style="F")
        self.set_xy(28 if self.show_mark else 18, 15.2)
        self.set_text_color(*INK)
        self.set_font("Helvetica", "B", 13)
        self.cell(100, 5.5, self.company, new_x=XPos.LEFT, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*MUTED)
        self.cell(100, 4.5, self.tagline)
        self.set_xy(110, 15.2)
        self.set_text_color(*BLUE)
        self.set_font("Helvetica", "B", 15)
        self.cell(82, 6, self.document_title.upper(), align="R", new_x=XPos.LEFT, new_y=YPos.NEXT)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*MUTED)
        self.cell(82, 4.5, self.reference, align="R")
        self.set_draw_color(*LINE)
        self.set_line_width(0.3)
        self.line(18, 28, 192, 28)
        self.set_y(33)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(
            0,
            5,
            latin1(f"Sample document · FabriSee demo data · Page {self.page_no()}"),
            align="C",
        )

    # --- building blocks -----------------------------------------------------------

    def label(self, text: str) -> None:
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 4.5, latin1(text.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def paragraph(self, text: str, *, size: float = 10, bold: bool = False) -> None:
        self.set_font("Helvetica", "B" if bold else "", size)
        self.set_text_color(*INK)
        self.multi_cell(0, 5, latin1(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def two_columns(self, left: list[tuple[str, str]], right: list[tuple[str, str]]) -> None:
        """Two blocks of `(label, value)` lines side by side."""
        top = self.get_y()
        bottoms = []
        for x, lines in ((18, left), (108, right)):
            self.set_xy(x, top)
            for index, (label, value) in enumerate(lines):
                self.set_x(x)
                if label:
                    self.set_font("Helvetica", "B", 8)
                    self.set_text_color(*MUTED)
                    self.cell(84, 4.5, latin1(label.upper()), new_x=XPos.LEFT, new_y=YPos.NEXT)
                    self.set_x(x)
                self.set_font("Helvetica", "B" if index == 0 else "", 10)
                self.set_text_color(*INK)
                self.multi_cell(84, 5, latin1(value), new_x=XPos.LEFT, new_y=YPos.NEXT)
            bottoms.append(self.get_y())
        self.set_y(max(bottoms) + 5)

    def bullet_list(self, items: list[str]) -> None:
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*INK)
        for item in items:
            self.set_x(18)
            self.cell(4, 5, "-")
            self.multi_cell(0, 5, latin1(item), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def data_table(
        self, headers: list[str], rows: list[list[str]], widths: tuple[float, ...], aligns
    ) -> None:
        self.set_draw_color(*LINE)
        self.set_text_color(*INK)
        self.set_font("Helvetica", "", 9.5)
        with self.table(
            col_widths=widths,
            text_align=aligns,
            borders_layout="HORIZONTAL_LINES",
            line_height=6.5,
            headings_style=self._heading_style(),
        ) as table:
            heading = table.row()
            for text in headers:
                heading.cell(latin1(text))
            for values in rows:
                row = table.row()
                for text in values:
                    row.cell(latin1(text))
        self.ln(3)

    def _heading_style(self):
        from fpdf.fonts import FontFace

        return FontFace(emphasis="BOLD", color=MUTED, fill_color=(248, 250, 252), size_pt=8.5)

    def to_bytes(self) -> bytes:
        return bytes(self.output())


def quotation_pdf(
    *,
    company: str,
    project_number: str,
    project_title: str,
    location: str,
    client_name: str,
    contact_name: str,
    client_address: str,
    version_no: int,
    issued_on: date,
    target_date: date,
    prepared_by: str,
    items: list[tuple[str, int, Decimal]],
    notes: str = "",
) -> bytes:
    """A quotation with line items. `items` are `(description, quantity, unit price)`."""
    pdf = SamplePDF(
        company=company,
        document_title="Quotation",
        reference=f"{project_number} · version {version_no}",
    )
    pdf.two_columns(
        [("Prepared for", client_name), ("", contact_name), ("", client_address)],
        [
            ("Project", f"{project_number} · {project_title}"),
            ("", f"Location: {location}"),
            ("", f"Target date: {long_date(target_date)}"),
        ],
    )
    pdf.two_columns(
        [("Date issued", long_date(issued_on))],
        [("Valid until", long_date(issued_on + timedelta(days=30)))],
    )

    rows, total = [], Decimal("0")
    for description, quantity, unit_price in items:
        amount = unit_price * quantity
        total += amount
        rows.append([description, str(quantity), money(unit_price), money(amount)])
    pdf.data_table(
        ["Description", "Qty", "Unit price (PHP)", "Amount (PHP)"],
        rows,
        widths=(92, 16, 33, 33),
        aligns=("LEFT", "RIGHT", "RIGHT", "RIGHT"),
    )
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*INK)
    pdf.cell(141, 8, "Total (PHP)", align="R")
    pdf.cell(33, 8, money(total), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    if notes:
        pdf.label("Notes")
        pdf.paragraph(notes)
        pdf.ln(3)
    pdf.label("Terms")
    pdf.bullet_list(
        [
            "Prices are in Philippine pesos and cover materials, fabrication, and the "
            "delivery and installation items listed above.",
            "This quotation is valid for 30 days from the date issued.",
            "Design work starts when the quotation is accepted in FabriSee. Production starts "
            "when all designated approvers approve a design revision.",
            "A change requested after design approval needs a new approved revision and, if "
            "the cost changes, an accepted revised quotation.",
        ]
    )
    pdf.ln(6)
    pdf.label("Prepared by")
    pdf.paragraph(prepared_by)
    return pdf.to_bytes()


def spec_sheet_pdf(
    *,
    company: str,
    project_number: str,
    project_title: str,
    client_name: str,
    revision_label: str,
    issued_on: date,
    designer: str,
    dimensions: str,
    materials: list[tuple[str, str, str]],
    notes: str = "",
) -> bytes:
    """A design specification sheet. `materials` are `(item, material and finish, size)`."""
    pdf = SamplePDF(
        company=company,
        document_title="Design spec sheet",
        reference=f"{project_number} · {revision_label}",
    )
    pdf.two_columns(
        [("Project", f"{project_number} · {project_title}"), ("", client_name)],
        [("Revision", revision_label), ("", f"Issued {long_date(issued_on)} by {designer}")],
    )
    pdf.label("Overall dimensions")
    pdf.paragraph(dimensions)
    pdf.ln(3)
    pdf.data_table(
        ["Item", "Material and finish", "Size"],
        [list(row) for row in materials],
        widths=(52, 82, 40),
        aligns=("LEFT", "LEFT", "LEFT"),
    )
    if notes:
        pdf.label("Notes for this revision")
        pdf.paragraph(notes)
        pdf.ln(3)
    pdf.label("Approval")
    pdf.paragraph(
        "This sheet belongs to the design revision above. Production follows the revision "
        "that all designated approvers approved in FabriSee (the approved design)."
    )
    return pdf.to_bytes()


def turnover_pdf(
    *,
    company: str,
    project_number: str,
    project_title: str,
    client_name: str,
    location: str,
    turned_over_on: date,
    turned_over_by: str,
    received_by: str,
    checklist: list[str],
) -> bytes:
    """A turnover checklist signed by both sides."""
    pdf = SamplePDF(company=company, document_title="Turnover checklist", reference=project_number)
    pdf.two_columns(
        [("Project", f"{project_number} · {project_title}"), ("", client_name)],
        [("Location", location), ("", f"Turned over on {long_date(turned_over_on)}")],
    )
    pdf.data_table(
        ["Checked", "Item"],
        [["Yes", item] for item in checklist],
        widths=(24, 150),
        aligns=("LEFT", "LEFT"),
    )
    pdf.ln(8)
    top = pdf.get_y()
    for x, role, name in (
        (18, "Turned over by", turned_over_by),
        (108, "Received by", received_by),
    ):
        pdf.set_draw_color(*LINE)
        pdf.line(x, top + 12, x + 74, top + 12)
        pdf.set_xy(x, top + 13)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*INK)
        pdf.cell(74, 5, latin1(name), new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(74, 4.5, role)
    return pdf.to_bytes()


def brief_pdf(
    *,
    company: str,
    title: str,
    reference: str,
    paragraphs: list[str],
    from_client: bool = False,
) -> bytes:
    """A short text document: a client's brief (`from_client`) or an internal note."""
    if from_client:
        pdf = SamplePDF(
            company=company,
            document_title=title,
            reference=reference,
            tagline="Client reference document",
            show_mark=False,
        )
    else:
        pdf = SamplePDF(company=company, document_title=title, reference=reference)
    for text in paragraphs:
        pdf.paragraph(text)
        pdf.ln(2)
    return pdf.to_bytes()
