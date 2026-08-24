"""Root URL configuration for the Team-D project."""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("events/", include("events.urls")),
    path("interactions/", include("interactions.urls")),
    path("search/", include("search.urls", namespace="search")),
    path("notifications/", include("notifications.urls", namespace="notifications")),
]