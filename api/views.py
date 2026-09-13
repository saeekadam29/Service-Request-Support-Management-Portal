from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, permissions
from rest_framework.exceptions import PermissionDenied

from tickets.models import Ticket, Category, Comment, TicketHistory
from .permissions import IsOwnerAgentOrAdmin
from .serializers import (
    TicketSerializer, TicketDetailSerializer, CategorySerializer, CommentSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), _AdminOnly()]
        return super().get_permissions()


class _AdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.profile.is_admin


class TicketViewSet(viewsets.ModelViewSet):
    """
    Provides list, retrieve, create, update, partial_update, destroy for tickets.

    GET  /api/tickets/            -> list (paginated, filterable, searchable)
    POST /api/tickets/            -> create
    GET  /api/tickets/{id}/       -> retrieve (includes comments + history)
    PUT  /api/tickets/{id}/       -> update
    DELETE /api/tickets/{id}/     -> delete
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerAgentOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'assigned_agent']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related('category', 'customer', 'assigned_agent')
        if user.profile.is_customer:
            return qs.filter(customer=user)
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TicketDetailSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_status, old_priority, old_agent = old_instance.status, old_instance.priority, old_instance.assigned_agent_id
        ticket = serializer.save()

        if ticket.status != old_status:
            TicketHistory.objects.create(
                ticket=ticket, actor=self.request.user,
                action=f"Status changed from {old_status} to {ticket.status} by {self.request.user.username} (via API)")
        if ticket.priority != old_priority:
            TicketHistory.objects.create(
                ticket=ticket, actor=self.request.user,
                action=f"Priority changed from {old_priority} to {ticket.priority} by {self.request.user.username} (via API)")
        if ticket.assigned_agent_id != old_agent:
            agent_name = ticket.assigned_agent.username if ticket.assigned_agent else "Unassigned"
            TicketHistory.objects.create(
                ticket=ticket, actor=self.request.user,
                action=f"Ticket assigned to {agent_name} by {self.request.user.username} (via API)")


class CommentViewSet(viewsets.ModelViewSet):
    """
    GET  /api/comments/?ticket=<id>  -> list comments for a ticket
    POST /api/comments/              -> add a comment
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['ticket']

    def get_queryset(self):
        user = self.request.user
        qs = Comment.objects.select_related('author', 'ticket')
        if user.profile.is_customer:
            qs = qs.filter(ticket__customer=user)
        return qs

    def perform_create(self, serializer):
        ticket = serializer.validated_data['ticket']
        user = self.request.user
        if user.profile.is_customer and ticket.customer_id != user.id:
            raise PermissionDenied("You cannot comment on another customer's ticket.")
        comment = serializer.save(author=user)
        TicketHistory.objects.create(
            ticket=comment.ticket, actor=user, action=f"{user.username} added a comment (via API)")
