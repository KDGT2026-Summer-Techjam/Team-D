from django.urls import path
from . import views

app_name = "interactions"

urlpatterns = [
    path("events/<int:pk>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("events/<int:pk>/like/", views.toggle_like, name="toggle_like"),
    path("events/<int:pk>/review/", views.submit_review, name="submit_review"),
]