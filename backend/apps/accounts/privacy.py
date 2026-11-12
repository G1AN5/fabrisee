"""The privacy notice shown at first sign-in (build guide, sections 10.1 and 16).

The wording lives in `privacy.md` so the group can review and edit it without touching
code. It uses a small subset of Markdown: `# Title`, `## Heading`, `- list item`, and
paragraphs. `{company_name}` is replaced with the company name from the settings.
"""

from functools import lru_cache
from pathlib import Path

NOTICE_FILE = Path(__file__).with_name("privacy.md")


def parse_notice(markdown: str) -> dict:
    """Turn the notice into `{"title": ..., "blocks": [...]}` for the React app.

    Blocks are `{"type": "heading" | "paragraph", "text": ...}` or
    `{"type": "list", "items": [...]}`.
    """
    title = ""
    blocks: list[dict] = []
    paragraph: list[str] = []
    items: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append({"type": "paragraph", "text": " ".join(paragraph)})
            paragraph.clear()

    def flush_list() -> None:
        if items:
            blocks.append({"type": "list", "items": list(items)})
            items.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
        elif line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            flush_paragraph()
            flush_list()
            blocks.append({"type": "heading", "text": line[3:].strip()})
        elif line.startswith("- "):
            flush_paragraph()
            items.append(line[2:].strip())
        elif items and raw_line.startswith((" ", "\t")):
            # A wrapped line of the current list item.
            items[-1] = f"{items[-1]} {line}"
        else:
            flush_list()
            paragraph.append(line)
    flush_paragraph()
    flush_list()
    return {"title": title, "blocks": blocks}


@lru_cache(maxsize=1)
def _notice_template() -> str:
    return NOTICE_FILE.read_text(encoding="utf-8")


def load_privacy_notice(company_name: str) -> dict:
    text = _notice_template()
    if company_name.endswith("."):
        # A name such as "Five Brothers Solutions Inc." already ends the sentence.
        text = text.replace("{company_name}.", company_name)
    return parse_notice(text.replace("{company_name}", company_name))
