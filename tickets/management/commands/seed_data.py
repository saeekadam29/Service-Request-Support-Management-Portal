import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from tickets.models import Category, Ticket, Comment


class Command(BaseCommand):
    help = "Seeds the database with demo users, categories, and sample tickets for local testing."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        categories = {}
        for name, desc in [
            ('Technical', 'Bugs, errors, and product malfunctions'),
            ('Account', 'Login, access and account management issues'),
            ('Billing', 'Invoices, payments and refunds'),
            ('Service', 'General service requests'),
            ('Other', 'Anything that does not fit the above'),
        ]:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            categories[name] = cat

        demo_users = [
            ('admin1', 'ADMIN', 'Admin@12345'),
            ('agent_riya', 'AGENT', 'Agent@12345'),
            ('agent_dev', 'AGENT', 'Agent@12345'),
            ('customer_amit', 'CUSTOMER', 'Customer@12345'),
            ('customer_priya', 'CUSTOMER', 'Customer@12345'),
        ]

        users = {}
        for username, role, password in demo_users:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': f'{username}@example.com',
            })
            if created:
                user.set_password(password)
                user.save()
            profile = user.profile
            profile.role = role
            profile.save()
            users[username] = user

        if Ticket.objects.count() == 0:
            sample_tickets = [
                ("Unable to reset password", "Password reset email never arrives.", 'Account', Ticket.Priority.HIGH),
                ("Invoice #4521 shows wrong amount", "Charged twice for the monthly plan.", 'Billing', Ticket.Priority.MEDIUM),
                ("App crashes on file upload", "500 error whenever uploading files over 5MB.", 'Technical', Ticket.Priority.CRITICAL),
                ("Request for onboarding call", "Would like a walkthrough of the dashboard.", 'Service', Ticket.Priority.LOW),
                ("Dark mode not saving preference", "Setting resets after logout.", 'Technical', Ticket.Priority.MEDIUM),
            ]
            customers = [users['customer_amit'], users['customer_priya']]
            agents = [users['agent_riya'], users['agent_dev']]

            for title, desc, cat_name, priority in sample_tickets:
                ticket = Ticket.objects.create(
                    title=title, description=desc, category=categories[cat_name],
                    priority=priority, customer=random.choice(customers),
                    assigned_agent=random.choice(agents + [None]),
                )
                Comment.objects.create(ticket=ticket, author=ticket.customer, body="Any update on this?")

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write("Demo login credentials:")
        for username, role, password in demo_users:
            self.stdout.write(f"  {role:9s} -> username: {username:16s} password: {password}")
