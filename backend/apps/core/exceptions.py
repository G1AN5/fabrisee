"""API error format and the exception raised by the process rules.

Every API error has the same shape::

    {"detail": "Plain-language message", "code": "machine_readable_code", "fields": {...}}

`fields` maps a field name to a list of messages and is empty unless input was invalid.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import exceptions
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as drf_exception_handler

GENERIC_FIELD_MESSAGE = "Please check the highlighted fields and try again."
NON_FIELD_KEYS = ("", "non_field_errors", "__all__")

STATUS_CODES = {
    401: "not_authenticated",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    429: "throttled",
}


class RuleViolation(exceptions.ValidationError):
    """A process rule (PR1 to PR9) rejected the action.

    `code` names the rule and the reason (for example ``PR5_NOT_ALL_APPROVED``), `message`
    is plain language for the user, and `fields` optionally maps field names to messages.
    """

    def __init__(self, code: str, message: str, fields: dict[str, str | list[str]] | None = None):
        self.rule_code = code
        self.message = message
        self.fields = {
            name: [value] if isinstance(value, str) else [str(item) for item in value]
            for name, value in (fields or {}).items()
        }
        super().__init__(detail=message, code=code)


def flatten_errors(detail, prefix: str = "") -> dict[str, list[str]]:
    """Flatten a DRF validation detail into ``{"field.path": ["message", ...]}``."""
    flat: dict[str, list[str]] = {}

    def add(path: str, messages: list[str]) -> None:
        flat.setdefault(path, []).extend(messages)

    if isinstance(detail, dict):
        for key, value in detail.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            for child_path, messages in flatten_errors(value, path).items():
                add(child_path, messages)
    elif isinstance(detail, (list, tuple)):
        if all(not isinstance(item, (dict, list, tuple)) for item in detail):
            add(prefix, [str(item) for item in detail])
        else:
            for index, item in enumerate(detail):
                if not item:
                    continue
                path = f"{prefix}.{index}" if prefix else str(index)
                for child_path, messages in flatten_errors(item, path).items():
                    add(child_path, messages)
    else:
        add(prefix, [str(detail)])
    return flat


def _validation_payload(exc: exceptions.ValidationError) -> dict:
    flat = flatten_errors(exc.detail)
    general: list[str] = []
    for key in NON_FIELD_KEYS:
        general.extend(flat.pop(key, []))
    detail = general[0] if general else GENERIC_FIELD_MESSAGE
    return {"detail": detail, "code": "validation_error", "fields": flat}


def api_exception_handler(exc, context):
    """Convert every handled exception into the FabriSee error format."""
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(detail=as_serializer_error(exc))

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, RuleViolation):
        payload = {"detail": exc.message, "code": exc.rule_code, "fields": exc.fields}
    elif isinstance(exc, exceptions.ValidationError):
        payload = _validation_payload(exc)
    else:
        code = STATUS_CODES.get(response.status_code, "error")
        if isinstance(exc, exceptions.APIException):
            codes = exc.get_codes()
            if isinstance(codes, str):
                code = codes
        detail = response.data.get("detail") if isinstance(response.data, dict) else None
        payload = {"detail": str(detail or "Something went wrong."), "code": code, "fields": {}}

    response.data = payload
    return response
