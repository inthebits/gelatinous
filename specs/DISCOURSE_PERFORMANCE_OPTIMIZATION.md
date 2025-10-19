# Discourse Performance Optimization
## Reducing Load Speed and Jitter

This document covers optimizations to reduce the loading jitter when navigating between gel.monster and forum.gel.monster.

---

## CSS Optimizations Applied

### 1. **Pre-allocated Space**
```css
body {
  padding-top: 80px;
}
```
- Reserves space BEFORE the iframe loads
- Prevents layout shift when header appears
- Eliminates vertical jitter

### 2. **Fixed Container Height**
```css
#gel-django-header-container {
  height: 80px; /* Prevents reflow */
}
```
- Browser knows exact dimensions immediately
- No recalculation when iframe loads

### 3. **CSS Containment**
```css
contain: layout style;
```
- Isolates iframe rendering from rest of page
- Reduces browser reflow/repaint work

### 4. **Will-Change Hint**
```css
will-change: contents;
```
- Tells browser to optimize this element
- Creates compositing layer for smoother updates

### 5. **Simplified Loading State**
- Removed `::before` pseudo-element with content
- Just shows solid background color
- Fewer DOM manipulations = faster render

---

## JavaScript Optimizations (in DISCOURSE_THEME_CODE_FIXED.md)

### Current Optimizations:
```javascript
// ✅ Single DOM check
if (document.getElementById('gel-django-header-container')) {
  return;
}

// ✅ Flag prevents double execution
if (window.iframeCreated) {
  return;
}
window.iframeCreated = true;
```

### Additional Recommended Optimizations:

#### 1. **Preconnect to Django Server**
Add to Discourse theme's `</head>` section:
```html
<link rel="preconnect" href="https://gel.monster">
<link rel="dns-prefetch" href="https://gel.monster">
```
- Establishes connection before iframe requests it
- Reduces DNS lookup time

#### 2. **Defer Non-Critical JavaScript**
In your JavaScript header:
```javascript
<script>
api.onPageChange(() => {
  // Your existing iframe creation code
  // Wrapped in requestIdleCallback for better performance
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => createHeaderIframe());
  } else {
    setTimeout(() => createHeaderIframe(), 1);
  }
});
</script>
```

#### 3. **Add Loading Attribute to Iframe**
```javascript
iframe.loading = 'eager'; // Prioritizes header loading
// OR
iframe.loading = 'lazy'; // If you prefer delayed loading
```

---

## Django Server Optimizations

### 1. **Cache the Header Template**
In your Django view for `/header_only/`:
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def header_only(request):
    # Your existing view code
    pass
```

### 2. **Enable HTTP/2**
- Ensure your server supports HTTP/2
- Multiplexes requests = faster iframe loading
- Check Lightsail configuration

### 3. **Minify Static Assets**
Ensure your Django static files are minified:
```python
# In settings.py
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
```

### 4. **Add Cache Headers**
In your header_only view:
```python
from django.views.decorators.cache import cache_control

@cache_control(max_age=900, public=True)  # 15 minutes
def header_only(request):
    # Your existing view code
    pass
```

---

## Discourse Configuration Optimizations

### 1. **Reduce Theme Component Count**
- Combine multiple theme components if possible
- Fewer components = fewer CSS files to load

### 2. **Use Color Palette Instead of CSS Variables**
- ✅ Already implemented!
- Color palette is compiled into Discourse's CSS
- Fewer runtime calculations

### 3. **Enable Discourse CDN**
If not already enabled:
- Admin → Settings → Files
- Configure CDN for static assets
- Speeds up all Discourse resources

---

## Quick Wins Checklist

**Immediate (CSS - already applied):**
- ✅ Pre-allocated space for header
- ✅ Fixed container height
- ✅ CSS containment and will-change
- ✅ Simplified loading state

**Easy (5 minutes):**
- [ ] Add preconnect/dns-prefetch links
- [ ] Cache Django header view
- [ ] Add cache headers to header_only

**Medium (15 minutes):**
- [ ] Implement requestIdleCallback wrapper
- [ ] Add iframe loading attribute
- [ ] Verify HTTP/2 is enabled

**Optional (if still seeing issues):**
- [ ] Minify Django static files
- [ ] Configure Discourse CDN
- [ ] Consolidate theme components

---

## Expected Results

After applying these optimizations:
- **Reduced initial jitter**: Pre-allocated space prevents layout shift
- **Faster iframe load**: Preconnect and caching reduce network time
- **Smoother transitions**: CSS containment isolates rendering
- **Better perceived performance**: Loading state is instant

---

## Measuring Performance

Use browser DevTools to measure improvements:

```javascript
// In browser console
performance.mark('discourse-start');
// Navigate to forum
performance.mark('discourse-end');
performance.measure('page-load', 'discourse-start', 'discourse-end');
console.log(performance.getEntriesByType('measure'));
```

Or use Lighthouse:
1. Open DevTools
2. Go to Lighthouse tab
3. Run audit on forum.gel.monster
4. Check "Performance" score

---

## Notes

The main jitter sources are:
1. **Layout shift** - Fixed with pre-allocated space ✅
2. **Network latency** - Minimize with caching and preconnect
3. **CSS application** - Reduced with color palette approach ✅
4. **JavaScript execution** - Optimize with idle callbacks

Most of the jitter should be eliminated with the CSS changes already applied!