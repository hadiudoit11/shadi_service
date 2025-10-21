# Auth0 Permissions Setup for Wedding App

This guide shows how to configure Auth0 roles and permissions for your wedding app instead of using hard-coded database permissions.

## Why Auth0 Permissions?

✅ **Centralized Authorization**: Manage all permissions in Auth0 dashboard
✅ **Real-time Updates**: Permission changes take effect immediately  
✅ **Scalable**: Add new roles/permissions without code changes
✅ **Secure**: Permissions verified with Auth0 tokens
✅ **Auditable**: Auth0 provides permission change logs

## Auth0 Setup Steps

### 1. Enable RBAC in Auth0

1. Go to Auth0 Dashboard > Settings > General
2. Enable "RBAC" (Role-Based Access Control)
3. Enable "Add Permissions in the Access Token"

### 2. Create Permissions

Go to Auth0 Dashboard > Applications > APIs > Create API (or use existing)

Add these permissions:

```
# Event Management
create:events        - Create wedding events
read:events          - View wedding events  
update:events        - Modify wedding events
delete:events        - Remove wedding events

# Vendor Management  
manage:vendors       - Full vendor management
read:vendors         - View vendor information

# Guest Management
manage:guests        - Full guest list management
read:guests          - View guest information
invite:guests        - Send wedding invitations

# Schedule Management
edit:schedules       - Modify wedding timeline
read:schedules       - View wedding schedule

# Analytics & Reports
access:analytics     - View wedding analytics
export:reports       - Export wedding reports

# Payment Management
manage:payments      - Handle wedding payments
view:payments        - View payment information

# Wedding Planning
plan:wedding         - Full wedding planning access
view:wedding         - View wedding information
```

### 3. Create Roles

Go to Auth0 Dashboard > User Management > Roles

Create these roles with associated permissions:

#### **Bride Role**
- `create:events`
- `read:events` 
- `update:events`
- `delete:events`
- `manage:vendors`
- `manage:guests`
- `invite:guests`
- `edit:schedules`
- `access:analytics`
- `export:reports`
- `manage:payments`
- `plan:wedding`
- `view:wedding`

#### **Groom Role** 
Same permissions as Bride

#### **Wedding Planner Role**
- `create:events`
- `read:events`
- `update:events`
- `manage:vendors`
- `read:vendors`
- `manage:guests`
- `invite:guests`
- `edit:schedules`
- `access:analytics`
- `plan:wedding`
- `view:wedding`

#### **Event Organizer Role**
- `create:events`
- `read:events`
- `update:events`
- `manage:vendors`
- `manage:guests`
- `edit:schedules`
- `access:analytics`

#### **Vendor Role**
- `read:events`
- `read:vendors`
- `read:schedules`
- `view:wedding`

#### **Guest Role**
- `read:events`
- `view:wedding`

### 4. Assign Roles to Users

1. Go to Auth0 Dashboard > User Management > Users
2. Select a user
3. Go to "Roles" tab
4. Assign appropriate role(s)

### 5. Configure Auth0 Application

Update your Auth0 application settings:

**Allowed Callback URLs:**
```
http://localhost:8000/auth/callback/,
https://yourdomain.com/auth/callback/
```

**JWT Configuration:**
- Enable "RS256" algorithm
- Add your API audience to get permissions in token

### 6. Update Django Settings

Add to your `.env` file:

```env
# Auth0 API Configuration (for Management API access)
AUTH0_AUDIENCE=https://your-api-identifier
AUTH0_MANAGEMENT_API_AUDIENCE=https://your-domain.auth0.com/api/v2/
```

## Testing Permissions

### 1. Assign Test Roles

1. Create test users in Auth0
2. Assign different roles (Bride, Groom, Vendor, etc.)
3. Test login and permission checks

### 2. API Testing

Test permission endpoints:

```bash
# Get user permissions
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/auth/api/permissions/

# Test vendor management (requires manage:vendors)
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/auth/api/vendors/

# Test analytics (requires access:analytics)  
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/auth/api/analytics/
```

### 3. Frontend Integration

```javascript
// Check permissions in frontend
const response = await fetch('/auth/api/permissions/');
const data = await response.json();

if (data.data.permissions.can_manage_vendors) {
    // Show vendor management UI
    showVendorManagement();
}

// Display user's Auth0 roles
console.log('User roles:', data.data.auth0_roles);
console.log('User permissions:', data.data.auth0_permissions);
```

## Permission Sync

The system automatically syncs permissions from Auth0:

- **On login**: Fresh permissions pulled from Auth0
- **Hourly**: Auto-sync if permissions are stale  
- **Manual**: Call `/auth/api/permissions/` POST to force sync

## Troubleshooting

### No Permissions Showing

1. Verify RBAC is enabled in Auth0
2. Check "Add Permissions in Access Token" is enabled
3. Ensure user has roles assigned
4. Verify API audience is configured

### Permission Denied Errors

1. Check user has correct role in Auth0
2. Verify role has required permissions
3. Check Auth0 Management API credentials
4. Look at Django logs for Auth0 API errors

### Sync Issues

1. Verify AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET
2. Check Auth0 Management API access
3. Ensure user has valid auth0_user_id

## Benefits of This Approach

1. **No Database Migrations**: Add new permissions without code changes
2. **Real-time**: Permission changes take effect immediately
3. **Centralized**: Manage all permissions in Auth0 dashboard
4. **Scalable**: Easy to add new roles for vendors, planners, etc.
5. **Secure**: Permissions verified with Auth0 tokens
6. **Auditable**: Auth0 tracks all permission changes

Your wedding app now uses Auth0's enterprise-grade RBAC instead of hard-coded permissions!