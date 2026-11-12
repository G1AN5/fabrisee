from django.urls import path

from apps.designs.views import ProjectRevisionsView
from apps.quotations.views import ProjectQuotationsView

from . import views

urlpatterns = [
    path("projects/", views.ProjectListView.as_view(), name="project-list"),
    path("projects/<int:pk>/", views.ProjectDetailView.as_view(), name="project-detail"),
    path(
        "projects/<int:pk>/timeline/",
        views.ProjectTimelineView.as_view(),
        name="project-timeline",
    ),
    path(
        "projects/<int:pk>/quotations/",
        ProjectQuotationsView.as_view(),
        name="project-quotations",
    ),
    path(
        "projects/<int:pk>/revisions/",
        ProjectRevisionsView.as_view(),
        name="project-revisions",
    ),
    path(
        "projects/<int:pk>/documents/",
        views.ProjectDocumentsView.as_view(),
        name="project-documents",
    ),
    path("files/<str:kind>/<int:pk>/", views.FileDownloadView.as_view(), name="file-download"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("approvals/pending/", views.PendingApprovalsView.as_view(), name="approvals-pending"),
]
