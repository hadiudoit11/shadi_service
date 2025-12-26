#!/usr/bin/env python
"""
One-time script to seed production database with vendors.
Run this in Render shell or as a job.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from authentication.models import Vendor, VendorCategory
from authentication.management.commands.import_vendors import Command as ImportCommand

# Check if vendors already exist
if Vendor.objects.exists():
    print(f"Production already has {Vendor.objects.count()} vendors")
else:
    print("Importing vendors to production...")
    
    # Run the import command
    cmd = ImportCommand()
    cmd.handle(csv_file='wedding_vendors_south_asian.csv')
    
    # Verify all vendors
    updated = Vendor.objects.update(is_verified=True, is_active=True)
    print(f"Verified {updated} vendors")
    
    print(f"Production now has {Vendor.objects.count()} vendors")