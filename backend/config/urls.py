from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from apps.core.views import api_not_found, spa_index

admin.site.site_header = "FabriSee administration"
admin.site.site_title = "FabriSee admin"
admin.site.index_title = "Records"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.projects.urls")),
    path("api/", include("apps.clients.urls")),
    path("api/", include("apps.notifications.urls")),
]

if "drf_spectacular" in settings.INSTALLED_APPS:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    ]

urlpatterns += [
    re_path(r"^api/", api_not_found),
    # Everything else belongs to the React app (client-side routing).
    re_path(r"^(?!api/|admin/|static/|media/).*$", spa_index, name="spa"),
]
