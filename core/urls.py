from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search_results, name="search_results"),
    path("events/new/", views.event_create, name="event_create"),
    path("events/<int:event_id>/", views.event_detail, name="event_detail"),
    path(
        "events/<int:event_id>/reviews/new/",
        views.review_create,
        name="review_create",
    ),
    path("reviews/<int:review_id>/", views.review_detail, name="review_detail"),
]
