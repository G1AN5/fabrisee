from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_models_and_migrations_are_in_sync():
    """Fails when a model changed without a new migration."""
    out = StringIO()

    try:
        call_command("makemigrations", "--check", "--dry-run", stdout=out, stderr=StringIO())
    except SystemExit as exit_error:  # pragma: no cover - only on failure
        pytest.fail(f"Missing migrations (exit {exit_error.code}):\n{out.getvalue()}")
