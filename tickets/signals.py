from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ticket, TicketHistory


@receiver(post_save, sender=Ticket)
def log_ticket_creation(sender, instance, created, **kwargs):
    """
    Automatically records a 'Ticket created' history entry the first time
    a Ticket row is saved. Updates (status change, assignment, etc.) are
    logged explicitly from the views, where we have access to the
    logged-in user performing the action.
    """
    if created:
        TicketHistory.objects.create(
            ticket=instance,
            actor=instance.customer,
            action=f"Ticket created by {instance.customer.username}",
        )
