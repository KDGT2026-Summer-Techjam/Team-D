"""Root URL configuration for the Team-D project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("core.urls")),
    path("events/", include("events.urls")),
    path("interactions/", include("interactions.urls")),
    path("search/", include("search.urls", namespace="search")),
    path("notifications/", include("notifications.urls", namespace="notifications")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
