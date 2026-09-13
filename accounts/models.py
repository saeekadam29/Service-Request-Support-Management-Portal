from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """
    Extends Django's built-in User model with a role field.
    One-to-One relationship: every User has exactly one Profile.
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        AGENT = 'AGENT', 'Support Agent'
        CUSTOMER = 'CUSTOMER', 'Customer'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)
    phone_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True, help_text="Relevant for Support Agents")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_agent(self):
        return self.role == self.Role.AGENT

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER
