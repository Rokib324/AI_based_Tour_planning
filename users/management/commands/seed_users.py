from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds initial test users with different roles'

    def handle(self, *args, **options):
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'admin123',
                'role': 'admin',
                'is_superuser': True,
                'is_staff': True,
            },
            {
                'username': 'client1',
                'email': 'client1@example.com',
                'password': 'client123',
                'role': 'client',
            },
            {
                'username': 'client2',
                'email': 'client2@example.com',
                'password': 'client123',
                'role': 'client',
            },
            {
                'username': 'manager1',
                'email': 'manager1@example.com',
                'password': 'manager123',
                'role': 'tour_manager',
                'is_staff': True,
            },
            {
                'username': 'manager2',
                'email': 'manager2@example.com',
                'password': 'manager123',
                'role': 'tour_manager',
                'is_staff': True,
            },
            {
                'username': 'finance1',
                'email': 'finance1@example.com',
                'password': 'finance123',
                'role': 'financial_approver',
                'is_staff': True,
            },
        ]

        for u_info in users_data:
            username = u_info['username']
            if not User.objects.filter(username=username).exists():
                is_superuser = u_info.get('is_superuser', False)
                is_staff = u_info.get('is_staff', False)
                
                if is_superuser:
                    user = User.objects.create_superuser(
                        username=username,
                        email=u_info['email'],
                        password=u_info['password'],
                        role=u_info['role'],
                    )
                else:
                    user = User.objects.create_user(
                        username=username,
                        email=u_info['email'],
                        password=u_info['password'],
                        role=u_info['role'],
                        is_staff=is_staff,
                    )
                self.stdout.write(self.style.SUCCESS(f"Successfully created user: {username} ({user.role})"))
            else:
                self.stdout.write(self.style.WARNING(f"User {username} already exists"))
