from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Decorator factory: role_required('ADMIN', 'AGENT') only allows those roles through.
    Raises PermissionDenied (HTTP 403) for anyone else, instead of silently
    redirecting, so unauthorized access is explicit and logged.
    """

    def check(user):
        if not user.is_authenticated:
            return False
        if user.profile.role not in roles:
            raise PermissionDenied("You do not have permission to access this page.")
        return True

    return user_passes_test(check)


def can_view_ticket(user, ticket):
    """Customers may only view their own tickets; Agents/Admins may view all."""
    if user.profile.is_admin:
        return True
    if user.profile.is_agent:
        return True
    return ticket.customer_id == user.id


def can_edit_ticket_status(user):
    """Only Agents and Admins can change ticket status/assignment."""
    return user.profile.is_admin or user.profile.is_agent
