#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path


def main():
    from config.env import load_env_file

    # Local configuration lives in the repository root (.env, never committed).
    load_env_file(Path(__file__).resolve().parent.parent / ".env")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django is not installed. Run `make setup` from the repository root first."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
