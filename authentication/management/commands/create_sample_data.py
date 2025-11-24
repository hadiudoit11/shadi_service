from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from authentication.models import Vendor, Service, Package

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for testing endpoints'

    def handle(self, *args, **options):
        # Create sample users
        bride = User.objects.create_user(
            username='jane@example.com',
            email='jane@example.com',
            first_name='Jane',
            last_name='Smith',
            password='testpass123'
        )
        bride.roles = ['bride']
        bride.wedding_date = date.today() + timedelta(days=180)
        bride.wedding_venue = 'Central Park'
        bride.guest_count_estimate = 150
        bride.auth0_roles = ['bride', 'event-organizer']
        bride.auth0_permissions = ['create:events', 'manage:guests', 'edit:schedules']
        bride.save()

        groom = User.objects.create_user(
            username='john@example.com',
            email='john@example.com', 
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        groom.roles = ['groom']
        groom.partner = bride
        groom.wedding_date = bride.wedding_date
        groom.wedding_venue = bride.wedding_venue
        groom.auth0_roles = ['groom', 'event-organizer']
        groom.auth0_permissions = ['create:events', 'manage:guests', 'edit:schedules']
        groom.save()
        
        bride.partner = groom
        bride.save()

        # Create vendor user
        vendor_user = User.objects.create_user(
            username='photographer@example.com',
            email='photographer@example.com',
            first_name='Sarah',
            last_name='Wilson',
            password='testpass123'
        )
        vendor_user.roles = ['vendor']
        vendor_user.auth0_roles = ['vendor']
        vendor_user.auth0_permissions = ['manage:vendors', 'access:analytics']
        vendor_user.save()

        # Create vendor business
        vendor = Vendor.objects.create(
            admin=vendor_user,
            business_name='Perfect Moments Photography',
            business_type='photographer',
            location_city='New York',
            location_state='NY',
            base_price=2500.00,
            description='Professional wedding photography with 20+ years experience'
        )

        # Create services
        photography_service = Service.objects.create(
            vendor=vendor,
            name='Wedding Photography Package',
            description='Full day wedding photography coverage',
            base_price=2500.00,
            category='photography',
            duration_hours=8,
            max_bookings_per_day=1
        )

        engagement_service = Service.objects.create(
            vendor=vendor,
            name='Engagement Session',
            description='Pre-wedding engagement photo session',
            base_price=500.00,
            category='photography',
            duration_hours=2,
            max_bookings_per_day=2
        )

        # Create package
        wedding_package = Package.objects.create(
            vendor=vendor,
            name='Complete Wedding Package',
            description='Wedding day photography plus engagement session',
            total_price=2800.00
        )

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data:\n'
                             f'- Bride: {bride.email}\n'
                             f'- Groom: {groom.email}\n' 
                             f'- Vendor: {vendor_user.email}\n'
                             f'- Vendor Business: {vendor.business_name}\n'
                             f'- Services: {photography_service.name}, {engagement_service.name}\n'
                             f'- Package: {wedding_package.name}')
        )