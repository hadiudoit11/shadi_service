# Auth0 Vendor Permissions with Organizations

This guide shows how to set up **Auth0 Organizations** for vendor businesses to have proper scoped permissions instead of hard-coded database permissions.

## Why Auth0 Organizations for Vendors?

✅ **Vendor-Scoped Permissions**: Each vendor business gets its own permission scope
✅ **Team Management**: Multiple users can work for one vendor with different roles  
✅ **Multi-Vendor Support**: One user can work for multiple vendor businesses
✅ **Enterprise-Grade**: Uses Auth0's organization features for B2B scenarios
✅ **Real-Time**: Permission changes take effect immediately

## Auth0 Organizations Setup

### 1. Enable Organizations

1. Go to Auth0 Dashboard > Organizations
2. Enable Organizations feature (Enterprise feature)
3. Create organizations for each vendor business

### 2. Create Vendor Organizations

For each vendor business:

```bash
# Example: Create organization for "Smith Photography"
Organization Name: Smith Photography
Organization ID: smith-photography  
Display Name: Smith Photography
```

### 3. Create Organization-Specific Roles

Create roles within each vendor organization:

#### **Vendor Owner Role**
- `read:vendor_info`
- `edit:vendor_info` 
- `manage:vendor_bookings`
- `respond:vendor_inquiries`
- `view:vendor_analytics`
- `manage:vendor_team`

#### **Vendor Manager Role**
- `read:vendor_info`
- `edit:vendor_info`
- `manage:vendor_bookings` 
- `respond:vendor_inquiries`
- `view:vendor_analytics`

#### **Vendor Employee Role**
- `read:vendor_info`
- `manage:vendor_bookings`
- `respond:vendor_inquiries`

#### **Vendor Representative Role**
- `read:vendor_info`
- `respond:vendor_inquiries`

### 4. Assign Users to Vendor Organizations

1. Go to Auth0 Dashboard > Organizations > [Vendor Org]
2. Add users to the organization
3. Assign appropriate roles within the organization

## Django Integration

### 1. Update Vendor Model

```python
class Vendor(models.Model):
    # ... existing fields
    auth0_organization_id = models.CharField(max_length=255, unique=True)
    
class VendorUser(models.Model):
    # ... existing fields  
    auth0_organization_id = models.CharField(max_length=255)
    auth0_role_id = models.CharField(max_length=255)
```

### 2. Organization Permission Checking

```python
# Check vendor-specific permissions
def can_edit_vendor_info(user, vendor):
    return Auth0VendorPermissionChecker.has_vendor_permission(
        user, vendor, 'edit:vendor_info'
    )

# Usage in views
@vendor_permission_required('edit:vendor_info')
def update_vendor_view(request, vendor_id):
    # Only users with edit:vendor_info for THIS vendor can access
    pass
```

### 3. Token Verification

Update token verification to include organization context:

```python
def verify_vendor_permission(user, vendor, permission):
    # Check if user's token includes permission for this vendor's organization
    organization_id = vendor.auth0_organization_id
    
    # Verify token has permission scoped to this organization
    return auth0_client.verify_organization_permission(
        user.auth0_access_token,
        organization_id, 
        permission
    )
```

## API Endpoints with Organization Permissions

### Vendor Business Management

```javascript
// Get vendor businesses user can manage
GET /auth/api/vendor-business/
// Returns vendors based on organization memberships

// Update specific vendor (requires organization membership)
PATCH /auth/api/vendor-business/123/
// Checks if user belongs to vendor's organization with edit permissions

// Respond to inquiry (requires organization membership)  
PATCH /auth/api/inquiries/456/respond/
// Checks if user can respond for vendor's organization
```

### Permission-Based UI

```javascript
// Frontend checks organization-scoped permissions
const vendorPermissions = await fetch(`/auth/api/vendor-permissions/${vendorId}/`);

if (vendorPermissions.can_edit_vendor_info) {
    showEditButton();
}

if (vendorPermissions.can_manage_team) {
    showTeamManagement();
}
```

## Auth0 Token Structure

With organizations, tokens include organization context:

```json
{
  "sub": "auth0|123",
  "email": "john@smithphoto.com",
  "org_id": "smith-photography",
  "permissions": [
    "edit:vendor_info",
    "manage:vendor_bookings",
    "respond:vendor_inquiries"
  ],
  "roles": ["Vendor Manager"]
}
```

## Benefits Over Database Permissions

### **Centralized Management**
- **All vendor permissions in Auth0**
- **No database permission fields**
- **Real-time permission updates**

### **Multi-Organization Support**
- **Users can work for multiple vendors**
- **Each vendor has isolated permissions**
- **Cross-vendor permission prevention**

### **Enterprise Features**
- **Organization invitations**
- **Team management in Auth0**
- **Audit logs of permission changes**

### **Scalability**
- **Add new vendor roles without code changes**
- **Automatic permission inheritance**
- **Easy vendor onboarding**

## Implementation Phases

### Phase 1: Basic Vendor Permissions (Current)
- Use local VendorUser relationships
- Auth0 permissions mapped to vendor roles
- Prepare for organization migration

### Phase 2: Auth0 Organizations (Future)
- Migrate to Auth0 Organizations
- Organization-scoped permissions
- Remove local permission logic

### Phase 3: Advanced Features (Future)
- Organization invitations
- Cross-vendor permissions
- Advanced team management

## Migration Strategy

1. **Start with local vendor permissions** (current implementation)
2. **Set up Auth0 Organizations** for existing vendors
3. **Migrate users** to organization memberships  
4. **Update permission checking** to use organization tokens
5. **Remove local permission fields** once fully migrated

This approach gives you enterprise-grade vendor permission management while maintaining flexibility for future scaling!