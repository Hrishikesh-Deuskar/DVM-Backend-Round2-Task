from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "dashboard/",
        views.dashboard_redirect,
        name="dashboard",
    ),
    path(
        "customer/",
        views.customer_dashboard,
        name="customer_dashboard",
    ),
    path(
        "organization/",
        views.organization_dashboard,
        name="organization_dashboard",
    ),
]