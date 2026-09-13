from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from .models import Category, Ticket


class TicketModelTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username='cust1', password='pass12345')
        self.customer.profile.role = Profile.Role.CUSTOMER
        self.customer.profile.save()
        self.category = Category.objects.create(name='Technical')

    def test_ticket_str(self):
        ticket = Ticket.objects.create(
            title='Cannot login', description='Login fails with 500 error',
            category=self.category, customer=self.customer)
        self.assertIn(str(ticket.id), str(ticket))

    def test_ticket_creation_logs_history(self):
        ticket = Ticket.objects.create(
            title='Cannot login', description='Login fails with 500 error',
            category=self.category, customer=self.customer)
        self.assertEqual(ticket.history.count(), 1)
        self.assertIn('created', ticket.history.first().action)


class TicketViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Billing')

        self.customer = User.objects.create_user(username='cust2', password='pass12345')
        self.customer.profile.role = Profile.Role.CUSTOMER
        self.customer.profile.save()

        self.other_customer = User.objects.create_user(username='cust3', password='pass12345')
        self.other_customer.profile.role = Profile.Role.CUSTOMER
        self.other_customer.profile.save()

        self.agent = User.objects.create_user(username='agent2', password='pass12345')
        self.agent.profile.role = Profile.Role.AGENT
        self.agent.profile.save()

        self.ticket = Ticket.objects.create(
            title='Refund not received', description='Refund pending for 10 days',
            category=self.category, customer=self.customer)

    def test_login_required_for_ticket_list(self):
        response = self.client.get(reverse('tickets:ticket_list'))
        self.assertEqual(response.status_code, 302)  # redirected to login

    def test_customer_can_create_ticket(self):
        self.client.login(username='cust2', password='pass12345')
        response = self.client.post(reverse('tickets:ticket_create'), {
            'title': 'New billing issue',
            'description': 'Charged twice for the same invoice',
            'category': self.category.id,
            'priority': Ticket.Priority.MEDIUM,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(title='New billing issue').exists())

    def test_customer_cannot_view_others_ticket(self):
        self.client.login(username='cust3', password='pass12345')
        response = self.client.get(reverse('tickets:ticket_detail', kwargs={'pk': self.ticket.pk}))
        self.assertEqual(response.status_code, 403)

    def test_agent_can_view_any_ticket(self):
        self.client.login(username='agent2', password='pass12345')
        response = self.client.get(reverse('tickets:ticket_detail', kwargs={'pk': self.ticket.pk}))
        self.assertEqual(response.status_code, 200)

    def test_agent_can_update_status(self):
        self.client.login(username='agent2', password='pass12345')
        response = self.client.post(reverse('tickets:ticket_update', kwargs={'pk': self.ticket.pk}), {
            'status': Ticket.Status.IN_PROGRESS,
            'priority': Ticket.Priority.HIGH,
            'assigned_agent': self.agent.id,
            'resolution_notes': '',
        })
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)
        self.assertEqual(self.ticket.history.count(), 4)  # created + status + priority + assigned
