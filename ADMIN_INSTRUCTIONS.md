# Django Admin Dashboard - Vendor Management Guide

## 🔐 Admin Login Information

**URL:** http://localhost:8000/admin/  
**Username:** `admin@example.com`  
**Password:** `admin123`  

> **Note:** If the above credentials don't work, you can create a new superuser:
> ```bash
> docker-compose exec web python manage.py createsuperuser
> ```

## 📋 Table of Contents
1. [Accessing the Admin Dashboard](#accessing-the-admin-dashboard)
2. [Managing Vendors](#managing-vendors)
3. [Managing Vendor Images](#managing-vendor-images)
4. [Managing Vendor Categories](#managing-vendor-categories)
5. [Bulk Operations](#bulk-operations)
6. [Troubleshooting](#troubleshooting)

---

## 1. Accessing the Admin Dashboard

### Step 1: Navigate to Admin URL
1. Open your browser
2. Go to: http://localhost:8000/admin/
3. You'll see the Django administration login page

### Step 2: Login
1. Enter username: `admin@example.com`
2. Enter password: `admin123`
3. Click "Log in"

### Step 3: Admin Dashboard Overview
After logging in, you'll see:
- **AUTHENTICATION** section with:
  - Event Users
  - Vendors
  - Vendor categories
  - Vendor images
  - Services
  - Packages
- **DJANGO ADMIN** section with:
  - Groups
  - Site administration

---

## 2. Managing Vendors

### 📍 Navigation
**Dashboard → AUTHENTICATION → Vendors**

### ➕ Adding a New Vendor

1. **Click "Vendors"** in the AUTHENTICATION section
2. **Click "ADD VENDOR +"** button (top right)
3. **Fill in required fields:**

   **Business Information:**
   - Business name* (e.g., "Elegant Photography Studio")
   - Business email* (e.g., "contact@elegantphoto.com")
   - Business phone (e.g., "416-555-0123")
   - Website (e.g., "https://elegantphoto.com")
   - Admin* (Select the user who manages this vendor)

   **Service Information:**
   - Category* (Select from dropdown: Photography, Catering, DJ, etc.)
   - Services offered (Click "+" to add services like "Wedding Photography", "Engagement Shoots")

   **Location:**
   - Address (e.g., "123 Queen St W")
   - City* (e.g., "Toronto")
   - State* (e.g., "Ontario")
   - Zip code (e.g., "M5H 2M9")
   - Service radius miles (Default: 25)

   **Business Details:**
   - Description (Detailed description of services)
   - Years in business (e.g., 10)
   - Insurance verified (Check if verified)
   - License number (if applicable)

   **Pricing:**
   - Price range min (e.g., 1500.00)
   - Price range max (e.g., 5000.00)
   - Pricing structure (Select: Hourly/Package/Per Guest/Flat Rate/Custom)

   **Status:**
   - Is active ✅ (Check to make vendor visible)
   - Is verified ✅ (Check to verify vendor)
   - Is featured ☐ (Check to feature on homepage)

4. **Scroll down to see "Vendor Images" inline section**
   - Click "Add another Vendor Image" to add images directly
   - Select image type (logo, portfolio, storefront hero, etc.)
   - Upload image or provide URL
   - Set display locations

5. **Click "SAVE"** (bottom right)

### ✏️ Editing an Existing Vendor

1. **Click "Vendors"** in the AUTHENTICATION section
2. **Find the vendor** using:
   - Search bar (search by name, email, city)
   - Filters (category, city, verified status)
3. **Click on the vendor name** to open edit page
4. **Make your changes**
5. **Choose save option:**
   - "Save" - Save and return to list
   - "Save and continue editing" - Save and stay on page
   - "Save and add another" - Save and create new vendor

### 🗑️ Deleting a Vendor

**Method 1: Individual Delete**
1. Click on the vendor name to edit
2. Click "DELETE" button (bottom left)
3. Confirm deletion on the confirmation page

**Method 2: Bulk Delete**
1. From vendor list, check boxes next to vendors to delete
2. Select "Delete selected vendors" from Action dropdown
3. Click "Go"
4. Confirm deletion

### 🔍 Searching and Filtering Vendors

**Use the search bar to find vendors by:**
- Business name
- Email
- City
- Category name

**Use filters (right sidebar) to filter by:**
- Category
- City  
- State
- Verified status
- Active status
- Featured status
- Price range

---

## 3. Managing Vendor Images

### 📍 Navigation
**Dashboard → AUTHENTICATION → Vendor images**

OR

**Within a vendor edit page → Vendor Images section (inline)**

### Adding Images to a Vendor

**Method 1: From Vendor Edit Page (Recommended)**
1. Edit the vendor
2. Scroll to "Vendor Images" section
3. Click "Add another Vendor Image"
4. Fill in:
   - Image type* (logo, portfolio, storefront hero, etc.)
   - Title (e.g., "Summer Wedding Setup")
   - Upload file or provide URL
   - Display locations (where image appears in UI)
   - Is primary (check for main image of that type)
5. Save the vendor

**Method 2: From Vendor Images Page**
1. Go to "Vendor images"
2. Click "ADD VENDOR IMAGE +"
3. Select vendor from dropdown
4. Fill in image details
5. Click "SAVE"

### Image Types Explained

- **logo** - Main business logo
- **profile_primary** - Main profile picture
- **storefront_hero** - Large banner for vendor page
- **storefront_thumbnail** - Small image for marketplace grid
- **portfolio** - General portfolio images
- **portfolio_featured** - Best work samples
- **venue_exterior/interior** - Venue photos

### Display Locations

Images can appear in multiple places:
- `marketplace_grid` - Vendor grid view
- `storefront_header` - Vendor page header
- `search_result` - Search results
- `mobile_card` - Mobile app view

---

## 4. Managing Vendor Categories

### 📍 Navigation
**Dashboard → AUTHENTICATION → Vendor categories**

### Default Categories Available

The system comes with 14 pre-configured categories:
- Photography
- Videography
- Catering
- DJ/Music
- Venue
- Florist
- Wedding Planner
- Makeup Artist
- Decorator
- Mehendi Artist
- Priest/Pandit
- Transportation
- Invitations
- Jewelry

### Adding a New Category

1. Click "ADD VENDOR CATEGORY +"
2. Fill in:
   - Name* (e.g., "Photo Booth")
   - Slug* (auto-generated, e.g., "photo-booth")
   - Description
   - Icon (CSS class, e.g., "fa-camera")
   - Is active ✅
3. Click "SAVE"

---

## 5. Bulk Operations

### Bulk Update Vendors

1. From vendor list, select multiple vendors
2. Choose action from dropdown:
   - **Mark as verified** - Verify multiple vendors
   - **Mark as unverified** - Unverify vendors
   - **Mark as featured** - Feature vendors
   - **Mark as active** - Activate vendors
   - **Mark as inactive** - Deactivate vendors
3. Click "Go"

### Export Vendor Data

1. Select vendors to export
2. Choose "Export selected" from actions
3. Select format (CSV, Excel, JSON)
4. Click "Go"

### Import Vendors from CSV

```bash
docker-compose exec web python manage.py import_vendors /path/to/vendors.csv
```

---

## 6. Troubleshooting

### Common Issues

**Can't log in to admin:**
```bash
# Reset admin password
docker-compose exec web python manage.py changepassword admin@example.com

# Or create new superuser
docker-compose exec web python manage.py createsuperuser
```

**CSS not loading in admin:**
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

**Vendor not showing on frontend:**
- Check "Is active" is checked
- Check "Is verified" is checked
- Check category is active

**Images not displaying:**
- Ensure AWS S3 credentials are configured in .env
- Check image URL is valid
- Verify display locations are set

### Quick Admin Actions

**Make all vendors verified:**
```python
# Django shell
docker-compose exec web python manage.py shell
from authentication.models import Vendor
Vendor.objects.update(is_verified=True)
```

**Feature top vendors:**
```python
# Feature vendors with 5+ years experience
from authentication.models import Vendor
Vendor.objects.filter(years_in_business__gte=5).update(is_featured=True)
```

---

## 📊 Admin Dashboard Features

### Vendor Statistics
From the vendor list page, you can see:
- Total number of vendors
- Number by category
- Verified vs unverified
- Active vs inactive

### Recent Actions
The admin dashboard shows your recent actions:
- Recently added vendors
- Recently edited vendors
- Recent deletions

### Search and Filter
Use advanced filters to find vendors:
- By location (city, state)
- By category
- By price range
- By verification status
- By active status

---

## 🔒 Security Notes

1. **Change default password** immediately in production
2. **Use strong passwords** (minimum 12 characters)
3. **Limit admin access** to trusted staff only
4. **Regular backups** of vendor data
5. **Monitor admin logs** for unusual activity

---

## 📱 Mobile Access

The Django admin is mobile-responsive. You can manage vendors from:
- Desktop browsers
- Tablets
- Mobile phones (limited functionality)

---

## 🆘 Getting Help

- **Documentation:** http://localhost:8000/api/docs/
- **API Schema:** http://localhost:8000/api/schema/
- **Django Admin Docs:** https://docs.djangoproject.com/en/stable/ref/contrib/admin/

---

## Quick Reference Card

| Task | Navigation | Action |
|------|------------|--------|
| Add vendor | Vendors → ADD VENDOR + | Fill form → Save |
| Edit vendor | Vendors → Click name | Edit → Save |
| Delete vendor | Vendors → Click name → DELETE | Confirm |
| Add images | Edit vendor → Vendor Images → Add | Upload → Save |
| Verify vendors | Vendors → Select → Actions → Mark as verified | Go |
| Feature vendor | Edit vendor → Is featured ✅ | Save |
| Search vendors | Vendors → Search bar | Type & Enter |
| Filter by category | Vendors → Filters → Category | Select |
| Bulk delete | Vendors → Select → Delete selected | Go → Confirm |

---

**Last Updated:** December 2024  
**Version:** 1.0  
**System:** Shadi Service Wedding Management Platform