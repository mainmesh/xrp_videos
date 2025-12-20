# Vercel Deployment Instructions

1. Make sure you have a `vercel.json` and `api/index.py` in your project root (already added).
2. Your Django settings are configured for Vercel (ALLOWED_HOSTS, static/media, etc.).
3. All dependencies are in `requirements.txt` (including `vercel-wsgi`).
4. On Vercel dashboard, create a new project and connect this repository.
5. Set the following environment variables in Vercel:
   - SECRET_KEY
   - DEBUG (set to false)
   - DATABASE_URL (for production database)
   - Any other required variables (e.g., STRIPE_API_KEY)
6. Set the build command to `pip install -r requirements.txt` (Vercel will auto-detect Python).
7. Deploy!

For static/media files, consider using an external storage (like AWS S3) for production.
