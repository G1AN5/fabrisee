from django.db.models import Case, IntegerField, Value, When

from apps.accounts.models import Role
from apps.projects.selectors import scoped_projects

from .models import DesignRevision, RevisionStatus


def scoped_revisions(user):
    """Design revisions the user may see (PR9), in the order that suits their role.

    Production staff build from the approved design, so they get the approved revision
    first, then the earlier revisions as history.
    """
    queryset = DesignRevision.objects.filter(project__in=scoped_projects(user))
    if user.role == Role.PRODUCTION:
        # TO CONFIRM: production staff do not see a revision that is still waiting for
        # approval, so nobody builds from a design the client has not approved.
        queryset = queryset.exclude(status=RevisionStatus.PENDING_APPROVAL)
        return queryset.annotate(
            approved_first=Case(
                When(status=RevisionStatus.APPROVED, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("project_id", "approved_first", "-revision_no")
    return queryset.order_by("project_id", "-revision_no")
