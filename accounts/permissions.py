from django.core.exceptions import PermissionDenied

from .models import OrganizationMembership


def require_organization_membership(user, organization_id, manager_only=False):

    if not user.is_authenticated:
        raise PermissionDenied

    if not user.groups.filter(name="Organization").exists():
        raise PermissionDenied

    memberships = OrganizationMembership.objects.filter(
        user=user,
        organization_id=organization_id,
    ).select_related("organization")

    if manager_only:
        memberships = memberships.filter(
            role=OrganizationMembership.Role.MANAGER
        )

    membership = memberships.first()

    if membership is None:
        raise PermissionDenied

    return membership