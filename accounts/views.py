from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render


@login_required
def dashboard_redirect(request):
    user = request.user

    if user.is_superuser:
        return redirect("admin:index")

    if user.groups.filter(name="Organization").exists():
        return redirect("accounts:organization_dashboard")

    if user.groups.filter(name="Customer").exists():
        return redirect("accounts:customer_dashboard")

    raise PermissionDenied


@login_required
def customer_dashboard(request):
    if not request.user.groups.filter(name="Customer").exists():
        raise PermissionDenied

    return render(
        request,
        "accounts/customer_dashboard.html",
    )


@login_required
def organization_dashboard(request):
    if not request.user.groups.filter(name="Organization").exists():
        raise PermissionDenied

    memberships = request.user.organization_memberships.select_related(
        "organization"
    )

    if not memberships.exists():
        raise PermissionDenied

    return render(
        request,
        "accounts/organization_dashboard.html",
        {"memberships": memberships},
    )