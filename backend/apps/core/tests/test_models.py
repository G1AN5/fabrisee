import pytest
from django.db.models import ProtectedError

from apps.core.models import QuotationDecisionMode, SystemSetting

pytestmark = pytest.mark.django_db


def test_system_settings_start_with_the_defaults_to_confirm():
    settings = SystemSetting.load()

    assert settings.company_name == "Five Brothers Solutions Inc."
    assert settings.project_number_prefix == "FS"
    assert settings.reminder_hours == 48
    assert settings.max_upload_mb == 20
    assert settings.quotation_decision_mode == QuotationDecisionMode.ANY_APPROVER


def test_system_settings_are_a_single_row():
    first = SystemSetting.load()
    first.reminder_hours = 24
    first.save()

    another = SystemSetting(reminder_hours=72)
    another.save()

    assert SystemSetting.objects.count() == 1
    assert SystemSetting.load().reminder_hours == 72


def test_system_settings_cannot_be_deleted():
    with pytest.raises(ProtectedError):
        SystemSetting.load().delete()
