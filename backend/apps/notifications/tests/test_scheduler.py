from io import StringIO

from django.core.management import call_command


def test_run_scheduler_once_runs_a_single_check():
    out = StringIO()

    call_command("run_scheduler", "--once", stdout=out)

    assert "Scheduler started" in out.getvalue()


def test_send_due_reminders_command_runs():
    out = StringIO()

    call_command("send_due_reminders", stdout=out)

    assert "Milestone 7" in out.getvalue()
