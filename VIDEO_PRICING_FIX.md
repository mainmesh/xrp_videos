# Video Pricing and Tier Display Fix

## Issues Identified

1. **Video prices showing $0** - The admin sets tier-specific prices, but the video list was displaying the default `video.reward` field (which is 0)
2. **Videos not displaying on front-end** - Need to ensure proper tier filtering and reward display
3. **Bronze, Silver, Gold tiers not showing in admin** - Tiers need to be created in the database first

## Fixes Applied

### 1. Template Filter for Tier-Based Rewards

Created a new template tag `get_video_reward` in [videos/templatetags/video_filters.py](videos/templatetags/video_filters.py) that:
- Takes a video and the user's current tier
- Returns the tier-specific reward amount from the `VideoTierPrice` model
- Falls back to the default reward if no tier-specific price exists

### 2. Updated Video List Template

Modified [templates/videos/list.html](templates/videos/list.html) to use the new template tag:
```django
<!-- Before -->
${{ v.reward }}

<!-- After -->
${% get_video_reward v user_tier %}
```

This now displays the correct price based on the user's tier membership.

### 3. Optimized Video Query

Updated [videos/views.py](videos/views.py) `video_list` function to prefetch tier prices:
```python
videos = Video.objects.filter(is_active=True).prefetch_related('tier_prices__tier')
```

This reduces database queries and ensures tier pricing data is available.

### 4. Created Default Tiers

Added management command and Python script to create default tiers:
- **Bronze** - $0 (Free tier)
- **Silver** - $10
- **Gold** - $25

## How to Fix Your System

### Step 1: Install Required Database Package

If using PostgreSQL (Neon):
```bash
pip install psycopg2-binary
```

Or add to your `requirements.txt`:
```
psycopg2-binary
```

Then install:
```bash
pip install -r requirements.txt
```

### Step 2: Create Default Tiers

**Option A: Using Django Management Command**
```bash
python manage.py create_default_tiers
```

**Option B: Using Python Script**
```bash
python create_tiers.py
```

**Option C: Using Django Shell**
```bash
python manage.py shell
```

Then run:
```python
from videos.models import Tier

# Create Bronze (Free)
Tier.objects.get_or_create(name='Bronze', defaults={'price': 0.0})

# Create Silver
Tier.objects.get_or_create(name='Silver', defaults={'price': 10.0})

# Create Gold
Tier.objects.get_or_create(name='Gold', defaults={'price': 25.0})
```

**Option D: Using Django Admin**
1. Go to `/admin/`
2. Click on "Tiers"
3. Add new tiers manually:
   - Bronze: $0
   - Silver: $10
   - Gold: $25

### Step 3: Add Videos with Tier Pricing

When adding a video in the admin panel:

1. Go to `/admin/videos/`
2. Click "Add New Video"
3. Fill in video details (title, URL, duration)
4. **Important**: Check the tiers you want to enable for this video
5. **Set the reward amount** for each selected tier (e.g., Bronze: $0.50, Silver: $1.00, Gold: $2.00)
6. Click "Add Video"

The system now requires at least one tier with a reward > $0 to be selected.

### Step 4: Verify Videos Display Correctly

1. Browse to `/videos/` as a logged-in user
2. You should now see correct reward amounts based on your user's tier
3. Videos should display with their tier-specific rewards

## Understanding the System

### Video Pricing Model

The system uses a flexible tier-based pricing model:

- **`Video.reward`**: Default reward (mostly deprecated, used as fallback)
- **`VideoTierPrice`**: Tier-specific pricing model with:
  - `video`: Foreign key to Video
  - `tier`: Foreign key to Tier (Bronze/Silver/Gold)
  - `reward`: The amount users earn at this tier for watching this video

### Example:

A video might have:
- Bronze tier: $0.25
- Silver tier: $0.75  
- Gold tier: $1.50

When a Bronze user views the video list, they see "$0.25"
When a Gold user views the same video, they see "$1.50"

## Troubleshooting

### Tiers Still Not Showing

1. Check database connection:
   ```bash
   python manage.py dbshell
   ```

2. Verify tiers exist:
   ```bash
   python manage.py shell
   >>> from videos.models import Tier
   >>> Tier.objects.all()
   ```

3. Check admin template is loading tiers correctly - look at browser console for JavaScript errors

### Videos Still Showing $0

1. Ensure you've set tier-specific rewards when creating the video
2. Check that the user has a tier assigned
3. Verify the template is using the new `get_video_reward` tag

### Videos Not Appearing

1. Check video `is_active` = True
2. Verify user's tier has access to the video
3. Check that `VideoTierPrice` records exist for the video

## Files Modified/Created

### Modified:
- [videos/templatetags/video_filters.py](videos/templatetags/video_filters.py) - Added reward filter
- [templates/videos/list.html](templates/videos/list.html) - Updated reward display
- [videos/views.py](videos/views.py) - Added prefetch_related for tier_prices

### Created:
- [videos/management/commands/create_default_tiers.py](videos/management/commands/create_default_tiers.py)
- [create_tiers.py](create_tiers.py) - Standalone script

## Production Deployment

When deploying to production (Vercel, Render, etc.):

1. Ensure database migrations are run:
   ```bash
   python manage.py migrate
   ```

2. Create tiers using the management command:
   ```bash
   python manage.py create_default_tiers
   ```

3. Test video upload and display functionality

4. Verify users see correct tier-based pricing

## Additional Notes

- The admin panel video form now validates that at least one tier with a reward > $0 is selected
- Videos without any tier pricing cannot be created
- The minimum required tier for a video is automatically set to the lowest-priced tier that has been enabled
- The template tag gracefully handles missing tier information and returns "0.00" as a fallback
