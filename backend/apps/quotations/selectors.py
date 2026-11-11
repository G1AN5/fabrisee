from apps.accounts.permissions import Capability, has_capability
from apps.projects.selectors import scoped_projects

from .models import Quotation


def scoped_quotations(user):
    """Quotations the user may see (PR9).

    Clients see only the versions that were sent to them, never drafts. Production staff
    do not see quotations at all.
    """
    if not has_capability(user, Capability.VIEW_QUOTATIONS):
        return Quotation.objects.none()
    queryset = Quotation.objects.filter(project__in=scoped_projects(user))
    if user.is_client_user:
        queryset = queryset.filter(sent_at__isnull=False)
    return queryset
