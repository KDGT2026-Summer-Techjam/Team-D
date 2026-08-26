from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("detail/<int:pk>/", views.event_detail, name="event_detail"),
    path("mine/favorites/", views.my_favorites, name="my_favorites"),
    path("mine/history/", views.my_view_history, name="my_view_history"),
]