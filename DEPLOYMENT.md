# Render Deployment Guide

This application is configured for deployment on Render. Follow these steps to deploy your Django application.

## Prerequisites

- A Render account (https://render.com)
- GitHub repository with your code pushed
- Environment variables configured

## Files Created for Deployment

1. **`Procfile`** - Specifies how to run the application
2. **`render.yaml`** - Infrastructure as Code for Render deployment
3. **`build.sh`** - Build script to run migrations and collect static files
4. **`requirements.txt`** - Updated with production dependencies:
   - `gunicorn` - WSGI HTTP Server
   - `whitenoise` - Static file serving
   - `python-decouple` - Environment variable management
   - `psycopg2-binary` - PostgreSQL adapter
5. **`xrp_site/settings.py`** - Updated with production configurations

## Deployment Steps

### Option 1: Using render.yaml (Recommended - Infrastructure as Code)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Connect to Render**
   - Go to https://render.com/dashboard
   - Click "New +" button
   - Select "Blueprint" 
   - Connect your GitHub repository
   - Authorize Render to access your GitHub

3. **Deploy Using Blueprint**
   - Render will automatically detect and read `render.yaml`
   - It will create:
     - PostgreSQL database
     - Web service with gunicorn
     - Static file serving via WhiteNoise
   - Click "Create resources"

### Option 2: Manual Deployment via Dashboard

1. **Create PostgreSQL Database**
   - Go to Render Dashboard → New → PostgreSQL
   - Name: `xrp_videos_db`
   - Use the provided connection string

2. **Create Web Service**
   - Go to Render Dashboard → New → Web Service
   - Connect your GitHub repository
   - Set Build Command:
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - Set Start Command:
     ```bash
     gunicorn xrp_site.wsgi
     ```
   - Add Environment Variables (see below)

## Environment Variables to Set on Render

Configure these in the Render dashboard under "Environment":

```
SECRET_KEY=<generate-a-strong-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.onrender.com,www.yourdomain.com
DATABASE_URL=<postgres-connection-string-from-database>
STRIPE_API_KEY=sk_test_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### How to Generate SECRET_KEY

Python:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use an online generator: https://djecrety.ir/

## Database Considerations

### Using PostgreSQL (Recommended for Production)

The app is configured to use PostgreSQL via `DATABASE_URL`. This is required for Render production deployments.

- Render automatically provides `DATABASE_URL` when you create a PostgreSQL database
- The settings automatically detect and use it

### Using SQLite (Local Development Only)

For local development without setting `DATABASE_URL`:
- The app defaults to SQLite (`db.sqlite3`)
- Suitable for testing but NOT for production on Render

## Post-Deployment Steps

1. **Create Superuser** (if needed)
   ```bash
   python manage.py createsuperuser
   ```
   Run this via Render Shell or use the Django admin interface

2. **Verify Static Files**
   - Visit your deployed URL
   - Check that CSS/JS/images load correctly
   - If not loading, run: `python manage.py collectstatic --noinput`

3. **Monitor Logs**
   - Go to your Render service dashboard
   - View logs for any errors

## Troubleshooting

### Static Files Not Loading
- Ensure `STATIC_ROOT` is properly configured
- Run `python manage.py collectstatic --noinput` via Render Shell
- Check WhiteNoise is in MIDDLEWARE

### Database Connection Error
- Verify `DATABASE_URL` environment variable is set
- Check database is running on Render
- Ensure `psycopg2-binary` is in requirements.txt

### SECRET_KEY Error
- Ensure `SECRET_KEY` is set in environment variables
- It should be a strong, random string
- Never commit it to version control

### 502 Bad Gateway
- Check application logs in Render dashboard
- Ensure migrations ran successfully
- Check for Python syntax errors

## Custom Domain Setup

1. **Purchase Domain** (if needed)
2. **In Render Dashboard**
   - Go to your Web Service settings
   - Scroll to "Custom Domains"
   - Add your domain
   - Follow DNS configuration instructions

## Scaling and Performance

For the free tier:
- 0.5 CPU, 512 MB RAM
- App spins down after 15 minutes inactivity
- Suitable for low-traffic projects

For production traffic:
- Upgrade to Starter or higher plan
- Consider separate database plan
- Add caching with Redis

## Additional Resources

- [Render Django Documentation](https://render.com/docs/deploy-django)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)
