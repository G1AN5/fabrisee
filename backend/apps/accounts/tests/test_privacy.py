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


def test_a_company_name_that_ends_with_a_period_is_not_followed_by_another():
    notice = load_privacy_notice("Five Brothers Solutions Inc.")

    texts = [block["text"] for block in notice["blocks"] if block["type"] == "paragraph"]
    assert texts[0].startswith(
        "FabriSee is the project coordination system of Five Brothers Solutions Inc. In line"
    )
    assert not any(".." in text for text in texts)
