from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class RegistrationTests(TestCase):
    def test_registration_creates_user_and_profile(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newcustomer',
            'email': 'newcustomer@example.com',
            'role': Profile.Role.CUSTOMER,
            'phone_number': '9999999999',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newcustomer')
        self.assertTrue(user.profile)
        self.assertEqual(user.profile.role, Profile.Role.CUSTOMER)

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(username='existing', email='dupe@example.com', password='pass12345')
        response = self.client.post(reverse('accounts:register'), {
            'username': 'another',
            'email': 'dupe@example.com',
            'role': Profile.Role.CUSTOMER,
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 200)  # form re-rendered with error
        self.assertFalse(User.objects.filter(username='another').exists())


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='agent1', password='pass12345')

    def test_valid_login(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'agent1',
            'password': 'pass12345',
        })
        self.assertEqual(response.status_code, 302)

    def test_invalid_login(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'agent1',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct")
