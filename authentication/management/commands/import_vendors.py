import csv
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from authentication.models import Vendor, VendorCategory
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Import wedding vendors from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='wedding_vendors_south_asian.csv',
            help='Path to CSV file (default: wedding_vendors_south_asian.csv)'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        
        # Check if file exists
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return

        # Get or create a default admin user for vendors
        admin_user, created = User.objects.get_or_create(
            username='vendor_admin',
            defaults={
                'email': 'vendor_admin@example.com',
                'first_name': 'Vendor',
                'last_name': 'Admin',
                'is_staff': True
            }
        )

        if created:
            self.stdout.write(f'Created admin user: {admin_user.email}')

        vendors_created = 0
        vendors_updated = 0
        errors = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Clean and extract data
                    name = row['name'].strip('"')
                    email = row['email'].strip('"')
                    phone = row['phone'].strip('"')
                    
                    # Handle address components
                    address = row['address'].strip('"')
                    city = row['city'].strip('"')
                    state = row['state'].strip('"')
                    zip_code = row['zip_code'].strip('"')
                    
                    # Build full address
                    full_address = f"{address}, {city}, {state} {zip_code}".strip()
                    
                    # Handle price (may be empty)
                    base_price_str = row['base_price'].strip('"')
                    base_price = float(base_price_str) if base_price_str else 0.0
                    
                    # Handle max_guests (may be empty)
                    max_guests_str = row['max_guests'].strip('"')
                    max_guests = int(max_guests_str) if max_guests_str else None
                    
                    description = row['description'].strip('"')
                    contact_name = row['contact_name'].strip('"')
                    website = row['website'].strip('"')
                    category = row['category'].strip('"')
                    amenities = row['amenities'].strip('"')
                    
                    # Handle boolean fields
                    is_active = row.get('is_active', 'TRUE').strip('"').upper() == 'TRUE'
                    is_featured = row.get('is_featured', 'FALSE').strip('"').upper() == 'TRUE'
                    
                    # Get or create vendor category
                    vendor_category, cat_created = VendorCategory.objects.get_or_create(
                        name=category,
                        defaults={
                            'slug': slugify(category),
                            'description': f'{category} services for weddings',
                            'is_active': True
                        }
                    )
                    
                    if cat_created:
                        self.stdout.write(f'Created category: {category}')
                    
                    # Parse amenities into services list
                    services_list = [s.strip() for s in amenities.split(',') if s.strip()] if amenities else []
                    
                    # Check if vendor exists (by business_name since many don't have emails)
                    vendor, created = Vendor.objects.get_or_create(
                        business_name=name,
                        defaults={
                            'admin': admin_user,
                            'business_email': email if email else f"{name.lower().replace(' ', '_')}@example.com",
                            'business_phone': phone,
                            'website': website,
                            'category': vendor_category,
                            'services_offered': services_list,
                            'address': full_address,
                            'city': city,
                            'state': state,
                            'zip_code': zip_code,
                            'description': description,
                            'price_range_min': base_price if base_price > 0 else None,
                            'pricing_structure': 'package' if base_price > 0 else 'custom',
                            'is_active': is_active,
                            'is_featured': is_featured,
                        }
                    )
                    
                    if created:
                        vendors_created += 1
                        self.stdout.write(f'✓ Created vendor: {name}')
                    else:
                        # Update existing vendor
                        vendor.business_name = name
                        vendor.business_phone = phone
                        vendor.website = website
                        vendor.category = vendor_category
                        vendor.services_offered = services_list
                        vendor.address = full_address
                        vendor.city = city
                        vendor.state = state
                        vendor.zip_code = zip_code
                        vendor.description = description
                        vendor.price_range_min = base_price if base_price > 0 else None
                        vendor.pricing_structure = 'package' if base_price > 0 else 'custom'
                        vendor.is_active = is_active
                        vendor.is_featured = is_featured
                        vendor.save()
                        
                        vendors_updated += 1
                        self.stdout.write(f'↻ Updated vendor: {name}')
                        
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error on row {row_num}: {str(e)}')
                    )
                    continue

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed:\n'
                f'  Created: {vendors_created} vendors\n'
                f'  Updated: {vendors_updated} vendors\n'
                f'  Errors: {errors} rows\n'
                f'  Total processed: {vendors_created + vendors_updated} vendors'
            )
        )