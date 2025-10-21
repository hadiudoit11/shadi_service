# Auth0 Django Setup Guide

This guide follows the official [Auth0 Django Quickstart](https://auth0.com/docs/quickstart/webapp/django).

## Prerequisites

- Python 3.8+
- Django 4.2+
- Authlib 1.0+

## Auth0 Configuration

### 1. Create Auth0 Application

1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. Create a new **Regular Web Application**
3. Note down:
   - **Domain**: `your-domain.auth0.com`
   - **Client ID**: Your application's client ID
   - **Client Secret**: Your application's client secret

### 2. Configure Application URLs

In your Auth0 application settings, set:

**Allowed Callback URLs:**
```
http://localhost:8000/auth/callback/
https://yourdomain.com/auth/callback/
```

**Allowed Logout URLs:**
```
http://localhost:8000/
https://yourdomain.com/
```

**Allowed Web Origins:**
```
http://localhost:8000
https://yourdomain.com
```

## Django Configuration

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in your project root:

```bash
cp .env.example .env
```

Update `.env` with your Auth0 credentials:

```env
# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id-here
AUTH0_CLIENT_SECRET=your-client-secret-here

# Django Settings
SECRET_KEY=your-django-secret-key
DEBUG=True
```

### 3. Database Setup

Run migrations for the custom user model:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

## Usage

### 1. Start Development Server

```bash
python manage.py runserver
```

### 2. Test Authentication

1. Visit `http://localhost:8000/auth/login/`
2. You'll be redirected to Auth0 for authentication
3. After successful login, you'll be redirected back to your app

### 3. Available Endpoints

**Authentication:**
- `/auth/login/` - Auth0 login
- `/auth/logout/` - Auth0 logout
- `/auth/callback/` - Auth0 callback (configured in Auth0 dashboard)
- `/auth/profile/` - User profile page
- `/auth/dashboard/` - User dashboard

**API Endpoints:**
- `/auth/api/profile/` - User profile management
- `/auth/api/partner/` - Wedding partner linking
- `/auth/api/roles/` - Role management
- `/auth/api/permissions/` - Permission management
- `/auth/api/wedding/` - Wedding data
- `/auth/api/events/` - Event management
- `/auth/api/vendors/` - Vendor management
- `/auth/api/guests/` - Guest management
- `/auth/api/schedule/` - Schedule management
- `/auth/api/analytics/` - Wedding analytics

## User Roles

The system supports multiple roles:

- **Bride/Groom**: Full wedding planning access
- **Organizer**: Event creation and management
- **Wedding Planner**: Professional planning access
- **Vendor**: Limited access to relevant features
- **Attendee**: Basic access

## Security Features

- Auth0 OAuth 2.0 authentication
- Session integrity validation
- Role-based permissions
- Secure session management
- Proper logout handling
- CSRF protection
- Environment variable configuration

## Troubleshooting

### Common Issues

1. **Callback URL Mismatch**: Ensure your Auth0 callback URLs match exactly
2. **Environment Variables**: Verify `.env` file is loaded correctly
3. **HTTPS Required**: Auth0 requires HTTPS in production
4. **Session Issues**: Clear browser cookies if experiencing login loops

### Debug Mode

Enable debug logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Production Deployment

1. Set `DEBUG = False`
2. Use HTTPS
3. Set secure session cookies
4. Use environment variables for secrets
5. Configure proper allowed hosts
6. Use a production database (PostgreSQL)

## Further Reading

- [Auth0 Django Documentation](https://auth0.com/docs/quickstart/webapp/django)
- [Authlib Django Integration](https://docs.authlib.org/en/latest/client/django.html)
- [Django Authentication Documentation](https://docs.djangoproject.com/en/stable/topics/auth/)