from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, serializers

from apps.core.exceptions import RuleViolation, api_exception_handler, flatten_errors


def handle(exc):
    return api_exception_handler(exc, {"view": None, "request": None})


def test_rule_violation_reports_rule_code_message_and_fields():
    response = handle(
        RuleViolation(
            "PR1_MISSING_REQUIRED_FIELDS",
            "Fill in the target date before submitting the request.",
            fields={"target_date": "Enter the target date."},
        )
    )

    assert response.status_code == 400
    assert response.data == {
        "detail": "Fill in the target date before submitting the request.",
        "code": "PR1_MISSING_REQUIRED_FIELDS",
        "fields": {"target_date": ["Enter the target date."]},
    }


def test_serializer_errors_are_flattened_per_field():
    response = handle(
        serializers.ValidationError(
            {"email": ["Enter a valid email address."], "non_field_errors": ["Passwords differ."]}
        )
    )

    assert response.status_code == 400
    assert response.data["code"] == "validation_error"
    assert response.data["detail"] == "Passwords differ."
    assert response.data["fields"] == {"email": ["Enter a valid email address."]}


def test_field_errors_without_general_message_get_a_generic_detail():
    response = handle(serializers.ValidationError({"title": ["This field is required."]}))

    assert response.data["detail"] == "Please check the highlighted fields and try again."
    assert response.data["fields"] == {"title": ["This field is required."]}


def test_django_validation_error_is_converted():
    response = handle(DjangoValidationError({"client": ["Choose the client."]}))

    assert response.status_code == 400
    assert response.data["fields"] == {"client": ["Choose the client."]}


def test_common_errors_have_stable_codes():
    assert handle(exceptions.NotAuthenticated()).data["code"] == "not_authenticated"
    assert handle(exceptions.PermissionDenied()).data["code"] == "permission_denied"
    assert handle(Http404()).data["code"] == "not_found"
    assert handle(exceptions.Throttled(wait=30)).data["code"] == "throttled"
    assert handle(Http404()).data["fields"] == {}


def test_unhandled_exceptions_are_left_to_django():
    assert handle(RuntimeError("boom")) is None


def test_flatten_errors_handles_nested_and_list_details():
    flat = flatten_errors(
        {"files": [{}, {"file": ["Too large."]}], "address": {"city": ["Required."]}}
    )

    assert flat == {"files.1.file": ["Too large."], "address.city": ["Required."]}
