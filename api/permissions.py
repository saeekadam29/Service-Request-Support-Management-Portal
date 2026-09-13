from rest_framework import permissions


class IsOwnerAgentOrAdmin(permissions.BasePermission):
    """
    Object-level permission for tickets:
    - Admins and Agents can view/edit any ticket.
    - Customers can only view/edit their own tickets (and only while Open).
    """

    def has_object_permission(self, request, view, obj):
        profile = request.user.profile
        if profile.is_admin or profile.is_agent:
            return True
        if request.method in permissions.SAFE_METHODS:
            return obj.customer_id == request.user.id
        # Write access for customers: only their own, only while still Open
        return obj.customer_id == request.user.id and obj.status == obj.Status.OPEN
