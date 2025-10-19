# Django Header Caching + Preconnect Setup Guide
## Reduce iframe loading jitter

This guide walks you through implementing server-side caching and browser preconnect hints to speed up the Django header iframe loading.

---

## Part 1: Django Side - Add Caching

### What Changed
The `header_only` view now includes HTTP cache headers:
```python
@cache_control(max_age=300, public=True)  # Cache for 5 minutes
```

### Why This Helps
- **Browser caches the HTML**: Subsequent loads are instant
- **CDN can cache it**: If you have a CDN, it can serve cached copies
- **5 minute duration**: Short enough to reflect auth changes, long enough to help performance

### Deploy to Production

**Option A: Direct edit on server**
```bash
ssh -i LightsailDefaultKey-us-west-2.pem ubuntu@play.gel.monster

# Edit the file
nano /home/ubuntu/gel.monster/gelatinous/web/website/views/header_only.py

# Add this after the imports:
from django.views.decorators.cache import cache_control

# Add decorator before the function:
@cache_control(max_age=300, public=True)

# Restart Evennia
cd /home/ubuntu/gel.monster
evennia reload
```

**Option B: Deploy from repository**
```bash
# Commit the changes
git add web/website/views/header_only.py
git commit -m "Add caching to header_only view for better iframe performance"
git push

# SSH to server and pull
ssh -i LightsailDefaultKey-us-west-2.pem ubuntu@play.gel.monster
cd /home/ubuntu/gel.monster
git pull
evennia reload
```

### Verify Caching Works
```bash
# Check the response headers
curl -I https://gel.monster/header-only/

# Look for:
# Cache-Control: max-age=300, public
```

---

## Part 2: Discourse Side - Add Preconnect Hints

### What to Add
In your Discourse theme's `</head>` section:
```html
<link rel="preconnect" href="https://gel.monster">
<link rel="dns-prefetch" href="https://gel.monster">
<div id="gel-django-header-container"></div>
```

### Why This Helps
- **preconnect**: Establishes full connection (DNS, TCP, TLS) before iframe loads
- **dns-prefetch**: Fallback for older browsers, resolves DNS early
- **Result**: When iframe requests the page, connection is already established

### Implementation Steps

1. **Go to Discourse Admin** → Customize → Themes
2. **Edit "Django Header Integration"** theme component
3. **Click "Edit HTML"** tab
4. **Select `</head>`** section
5. **Update the HTML** to include the preconnect lines (as shown above)
6. **Save**
7. **Hard refresh** your browser (Cmd+Shift+R)

---

## Expected Performance Improvement

### Before:
1. Browser starts loading Discourse page
2. JavaScript creates iframe
3. Browser discovers it needs to connect to gel.monster
4. DNS lookup (~20-100ms)
5. TCP handshake (~20-50ms)
6. TLS handshake (~50-100ms)
7. Request header HTML (~50-200ms)
8. **Total: 140-450ms** → visible jitter

### After:
1. Browser starts loading Discourse page
2. **Preconnect immediately starts connecting to gel.monster** (parallel)
3. JavaScript creates iframe
4. Connection already established ✅
5. Request header HTML (from cache: ~10-50ms)
6. **Total: 10-50ms** → much smoother

---

## Tuning Cache Duration

If you want different cache times:

**Longer cache (less jitter, slower auth updates):**
```python
@cache_control(max_age=900, public=True)  # 15 minutes
```

**Shorter cache (faster auth updates, more jitter):**
```python
@cache_control(max_age=60, public=True)  # 1 minute
```

**Vary by authentication (different cache per user state):**
```python
from django.views.decorators.vary import vary_on_cookie

@vary_on_cookie
@cache_control(max_age=300, public=False, private=True)
def header_only(request):
    # ...
```

---

## Troubleshooting

### Cache not working?
```bash
# Check if headers are present
curl -I https://gel.monster/header-only/

# If you see "Cache-Control: no-cache" or no Cache-Control header:
# 1. Verify the decorator is applied
# 2. Check if Django caching middleware is interfering
# 3. Restart Evennia
```

### Preconnect not working?
- Open browser DevTools → Network tab
- Filter by "gel.monster"
- Look at the first request timing
- "Initial connection" should be very fast (< 10ms) if preconnect worked

### Still seeing jitter?
The remaining jitter is likely:
1. **HTML render time**: The Django header still needs to render
2. **Static assets**: CSS/images in the header need to load
3. **Network latency**: Physical distance to server

Consider also:
- Using a CDN for static assets
- Inlining critical CSS in header_only.html
- Reducing header complexity

---

## Quick Checklist

- [ ] Update Django view with cache decorator
- [ ] Deploy to production server
- [ ] Verify cache headers with curl
- [ ] Add preconnect links to Discourse theme
- [ ] Save and refresh Discourse
- [ ] Test loading speed improvement

---

## Notes

- **5 minutes** is a good balance for most cases
- **Authentication changes** take up to 5 minutes to reflect in cached headers
- **Logged-in users** may want `vary_on_cookie` to see their auth state immediately
- **Preconnect** is free performance - no downside to using it

The combination of caching + preconnect should significantly reduce the iframe loading jitter!