# Production Deployment Setup (Render)

## 🔧 Environment Variables Required

Set these environment variables in your Render dashboard:

### Core Django Settings
```
SECRET_KEY=your-super-secret-production-key-here-minimum-50-chars
DEBUG=False
```

### Database (Auto-configured by Render PostgreSQL)
```
DATABASE_URL=postgresql://user:password@host:port/database
```

### Auth0 Configuration
```
AUTH0_DOMAIN=carrot-erp.us.auth0.com
AUTH0_CLIENT_ID=B5hRQPCYBOtV7lN3jUIVg2b3PDkjy2hD
AUTH0_CLIENT_SECRET=your-auth0-client-secret
```

### AWS S3 (for image uploads)
```
USE_S3=True
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=shadi-s3-bucket-sh
AWS_S3_REGION_NAME=us-east-1
```

---

## 🐛 Current Issues & Solutions

### Issue 1: Database SSL Connection Error
**Error:** `SSL connection has been closed unexpectedly`

**Solution Applied:**
- Added SSL mode requirement for production PostgreSQL
- Updated database configuration with proper SSL settings

**Code Fix:**
```python
# In settings.py - SSL configuration for Render PostgreSQL
if not DEBUG and os.getenv('DATABASE_URL'):
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }
```

### Issue 2: Static Files (CSS) Not Loading  
**Error:** Admin panel has no styling, CSS files return 404

**Solutions Applied:**
- Added WhiteNoise middleware for serving static files
- Configured static file compression
- Set proper STATIC_URL and STATIC_ROOT

**Code Fix:**
```python
# Added to MIDDLEWARE
'whitenoise.middleware.WhiteNoiseMiddleware',

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## 🚀 Deployment Steps

### 1. Commit and Push Changes
```bash
git add .
git commit -m "Fix production database SSL and static files configuration"
git push origin main
```

### 2. Configure Render Environment Variables
In your Render dashboard:
1. Go to your service settings
2. Click "Environment" tab
3. Add all the environment variables listed above
4. **Important:** Set `DEBUG=False` for production

### 3. Trigger Deployment
The push to main should trigger an automatic deployment on Render.

### 4. Run Database Migrations (if needed)
After deployment, you may need to run:
```bash
# From Render shell or as a one-time script
python manage.py migrate
python manage.py collectstatic --noinput
```

### 5. Create Superuser (if needed)
```bash
# From Render shell
python manage.py createsuperuser
```

---

## 🔐 Security Configuration

### Production Security Headers
The following security settings are automatically applied when `DEBUG=False`:

- XSS Protection enabled
- Content type sniffing disabled  
- HTTPS strict transport security (HSTS)
- Secure cookies (HTTPS only)
- CSRF protection with secure cookies
- Proper referrer policy

### CORS Configuration
Production CORS is configured for:
- Frontend domains (update in `CORS_ALLOWED_ORIGINS`)
- Secure credentials handling
- Proper header allowlist

---

## 📝 Post-Deployment Checklist

### ✅ Verify Database Connection
1. Visit: `https://shadi-service.onrender.com/admin/`
2. Should load without SSL errors
3. Should show proper Django admin styling

### ✅ Test Admin Login
1. Try logging in with superuser credentials
2. Verify vendor management works
3. Check that CSS is loading properly

### ✅ Test API Endpoints
1. `GET https://shadi-service.onrender.com/auth/api/vendors/` 
2. `GET https://shadi-service.onrender.com/auth/api/vendors/categories/`
3. `GET https://shadi-service.onrender.com/api/docs/` (API documentation)

### ✅ Test Auth0 Integration
1. Visit: `https://shadi-service.onrender.com/auth/login/`
2. Should redirect to Auth0 login page
3. Test login flow and callback

### ✅ Test Image Uploads
1. Login to admin panel
2. Try uploading vendor images
3. Verify S3 integration works

---

## 🛠️ Debugging Production Issues

### Check Render Logs
1. Go to Render dashboard
2. Click on your service
3. Check "Logs" tab for errors

### Common Log Errors & Solutions

**SSL Connection Error:**
- Verify `DATABASE_URL` environment variable is set
- Check that SSL mode is configured properly

**Static Files 404:**
- Ensure WhiteNoise middleware is properly configured
- Run `python manage.py collectstatic` manually

**CORS Errors:**
- Add your frontend domain to `CORS_ALLOWED_ORIGINS`
- Ensure credentials are allowed if needed

**Auth0 Redirect Issues:**
- Update Auth0 dashboard callback URLs for production domain
- Verify Auth0 environment variables are set correctly

### Manual Commands on Render

To run Django commands on Render:
1. Go to your service dashboard
2. Click "Shell" tab (if available)
3. Or use Render's one-time job feature

---

## 🔗 Important URLs

### Production URLs
- **Admin Panel:** https://shadi-service.onrender.com/admin/
- **API Documentation:** https://shadi-service.onrender.com/api/docs/
- **Auth0 Login:** https://shadi-service.onrender.com/auth/login/
- **API Base:** https://shadi-service.onrender.com/auth/api/

### Auth0 Configuration
Update your Auth0 dashboard with production URLs:
- **Callback URL:** `https://shadi-service.onrender.com/auth/callback/`
- **Logout URL:** `https://shadi-service.onrender.com/`
- **Allowed Origins:** `https://shadi-service.onrender.com`

---

## 📈 Monitoring

### Health Check Endpoint
Create a simple health check:
```
GET https://shadi-service.onrender.com/auth/api/vendors/
```
Should return vendors list if everything is working.

### Performance Monitoring
- Monitor Render metrics dashboard
- Watch for memory/CPU usage spikes
- Monitor database connection counts

---

## 🚨 Emergency Procedures

### If Site is Down
1. Check Render service status
2. Check environment variables are set correctly
3. Review recent deployment logs
4. Rollback to previous deployment if needed

### If Database Issues Persist
1. Verify Render PostgreSQL service is running
2. Check DATABASE_URL format
3. Test database connection manually

### If Static Files Issues Continue
1. Manually run `python manage.py collectstatic`
2. Clear browser cache
3. Check WhiteNoise middleware configuration

---

**Last Updated:** December 2024  
**Status:** Configured for SSL and static files fixes