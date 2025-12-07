# Admin Panel Setup on Render

## The Problem
You're getting "Invalid username or password" because the admin user doesn't exist in the **production database** on Render (it only exists in your local database).

## Solution: Run the Admin Creation Command on Render

### Step 1: Go to Render Dashboard
1. Go to https://dashboard.render.com/
2. Click on your **xrp_videos** web service

### Step 2: Open the Shell
1. Click the **Shell** tab at the top
2. Wait for the shell to connect (you'll see a terminal prompt)

### Step 3: Run the Admin Creation Command
In the Render shell, type this command:

```bash
python manage.py create_admin
```

You should see output like:
```
✓ Admin user "admin" password reset successfully!
  Username: admin
  Password: admin123
  Staff: True
  Superuser: True
```

### Step 4: Login to Admin Panel
Now you can login at:
**https://xrp-videos.onrender.com/admin/login/**

**Credentials:**
- Username: `admin`
- Password: `admin123`

---

## Features Added
✅ **Password visibility toggle** - Click the eye icon to see your password
✅ **Management command** - Easy admin creation/reset command
✅ **Better error messages** - Clear feedback on login issues

---

## For Future Reference
If you ever need to reset the admin password on Render:
1. Go to Render Dashboard → Your service → Shell
2. Run: `python manage.py create_admin`

This works on both local and production databases!
