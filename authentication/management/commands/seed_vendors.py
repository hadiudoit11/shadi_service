from django.core.management.base import BaseCommand
from authentication.models import Vendor, VendorCategory
import csv
import os


class Command(BaseCommand):
    help = 'Seed production database with vendors from CSV'

    def handle(self, *args, **options):
        # Check if vendors already exist
        if Vendor.objects.exists():
            self.stdout.write(self.style.WARNING('Vendors already exist. Skipping seed.'))
            return

        csv_path = os.path.join(os.path.dirname(__file__), '../../..', 'wedding_vendors_south_asian.csv')
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found at {csv_path}'))
            return

        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            created_count = 0
            
            for row in reader:
                # Get or create category
                category_name = row.get('Category', '').strip()
                category = None
                if category_name:
                    category, _ = VendorCategory.objects.get_or_create(
                        name=category_name,
                        defaults={'slug': category_name.lower().replace(' & ', '-').replace(' ', '-')}
                    )
                
                # Create vendor
                vendor, created = Vendor.objects.get_or_create(
                    business_name=row.get('Business Name', '').strip(),
                    defaults={
                        'category': category,
                        'location': row.get('Location', '').strip(),
                        'city': row.get('City', '').strip(),
                        'state': row.get('State', '').strip(),
                        'description': row.get('Description', '').strip(),
                        'website': row.get('Website', '').strip(),
                        'business_phone': row.get('Business Phone', '').strip(),
                        'is_verified': True,  # Auto-verify for production
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    
                    # Parse services
                    services = row.get('Services Offered', '').strip()
                    if services:
                        vendor.services_offered = [s.strip() for s in services.split(',')]
                        vendor.save()
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} vendors'))