from django.core.management.base import BaseCommand
from authentication.models import EventUser


class Command(BaseCommand):
    help = 'Assign Auth0 roles to users for testing (simulates Auth0 role assignment)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')
        parser.add_argument('roles', nargs='+', help='Roles to assign')
        parser.add_argument(
            '--permissions',
            nargs='*',
            help='Permissions to assign',
            default=[]
        )

    def handle(self, *args, **options):
        email = options['email']
        roles = options['roles']
        permissions = options['permissions']

        try:
            user = EventUser.objects.get(email=email)
        except EventUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} does not exist')
            )
            return

        # Update roles
        user.auth0_roles = roles
        
        # Update permissions if provided
        if permissions:
            user.auth0_permissions = permissions
        
        # Set sync time to now
        from django.utils import timezone
        user.last_auth0_sync = timezone.now()
        
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully assigned roles {roles} to {email}'
            )
        )
        
        if permissions:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully assigned permissions {permissions} to {email}'
                )
            )