from apps.accounts.privacy import load_privacy_notice, parse_notice


def test_parse_notice_reads_headings_paragraphs_and_lists():
    notice = parse_notice(
        "# Title\n\nFirst line\ncontinues here.\n\n"
        "## Section\n\n- One\n- Two wraps\n  onto a line\n\nLast."
    )

    assert notice == {
        "title": "Title",
        "blocks": [
            {"type": "paragraph", "text": "First line continues here."},
            {"type": "heading", "text": "Section"},
            {"type": "list", "items": ["One", "Two wraps onto a line"]},
            {"type": "paragraph", "text": "Last."},
        ],
    }


def test_notice_covers_what_why_who_and_rights():
    notice = load_privacy_notice("Sample Company")

    headings = [block["text"] for block in notice["blocks"] if block["type"] == "heading"]
    assert headings == ["What FabriSee keeps", "Why it is kept", "Who can see it", "Your rights"]
    assert "Sample Company" in notice["blocks"][0]["text"]
