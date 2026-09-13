from django.conf import settings
from django.db import models
from django.urls import reverse


class Category(models.Model):
    """Ticket category, e.g. Technical, Billing. Managed by Admins."""
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ticket(models.Model):
    """
    Core model of the application. Represents one customer service request.
    """

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='tickets')
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='tickets_created', help_text="The customer who raised this ticket",
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets_assigned', limit_choices_to={'profile__role': 'AGENT'},
    )
    resolution_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} - {self.title}"

    def get_absolute_url(self):
        return reverse('tickets:ticket_detail', kwargs={'pk': self.pk})

    @property
    def is_open(self):
        return self.status in (self.Status.OPEN, self.Status.IN_PROGRESS)


class Comment(models.Model):
    """A comment/note left on a ticket by any participant (customer, agent, admin)."""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on Ticket #{self.ticket_id}"


class TicketHistory(models.Model):
    """
    Audit trail of important events on a ticket, e.g. 'Status changed from
    Open to In Progress'. Automatically populated via signals - see signals.py.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Ticket histories'

    def __str__(self):
        return f"[Ticket #{self.ticket_id}] {self.action}"
