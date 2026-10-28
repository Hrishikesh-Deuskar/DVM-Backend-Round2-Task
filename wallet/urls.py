from django.urls import path

from . import views


app_name = "wallet"

urlpatterns = [
    path(
        "",
        views.wallet_dashboard,
        name="dashboard",
    ),
]