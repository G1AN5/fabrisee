"""Paths in the React app (used for notification deep links and emails)."""

# section -> tab segment in the staff workspace
STAFF_TABS = {
    "overview": "",
    "quotation": "quotations",
    "design": "revisions",
    "progress": "progress",
    "documents": "documents",
    "activity": "activity",
}
# section -> tab segment in the client portal
PORTAL_TABS = {
    "overview": "",
    "quotation": "quotation",
    "design": "designs",
    "progress": "progress",
    "documents": "documents",
    "activity": "progress",
}


def project_path(user, project, section: str = "overview") -> str:
    """The page of `project` for `user`.

    For example `/app/projects/12/revisions` for staff and `/portal/projects/12/designs`
    for a client user.
    """
    if user.is_client_user:
        base, tab = f"/portal/projects/{project.pk}", PORTAL_TABS[section]
    else:
        base, tab = f"/app/projects/{project.pk}", STAFF_TABS[section]
    return f"{base}/{tab}" if tab else base
