from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser for Django admin access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@shadi.com',
            help='Admin email (default: admin@shadi.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Admin password (default: admin123)'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        # Check if superuser already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser with email {email} already exists')
            )
            return
        
        # Create superuser
        user = User.objects.create_superuser(
            username=email,
            email=email,
            password=password,
            first_name='Admin',
            last_name='User'
        )
        
        # Set additional fields for EventUser
        user.roles = ['admin']
        user.subscription_tier = 'premium'
        user.subscription_active = True
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created superuser:\n'
                f'  Email: {email}\n'
                f'  Password: {password}\n'
                f'  Access admin at: http://localhost:8000/admin/'
            )
        )