from django.contrib.auth import views as auth_views
from django.urls import path

from .views import AccountDeleteView, PreferenceView, ProfileView, SignupView

app_name = "accounts"

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("preferences/", PreferenceView.as_view(), name="preferences"),
    path("delete/", AccountDeleteView.as_view(), name="delete"),
]
