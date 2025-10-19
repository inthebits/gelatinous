# Discourse Header Iframe Implementation
## Seamless Django Header Integration

**Date**: October 19, 2025  
**Status**: Ready for Implementation  
**Objective**: Embed Django header in Discourse forum via iframe for 100% visual consistency

---

## Overview

This implementation embeds the Django header from `gel.monster` into the Discourse forum at `forum.gel.monster` using an iframe. When properly configured, users cannot tell it's an iframe - it appears as a native header with full functionality.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ forum.gel.monster (Discourse)                           │
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │ <iframe src="gel.monster/header-only/">        │   │
│  │   Django Header (Full Functionality)           │   │
│  │   - Authentication state                       │   │
│  │   - Navigation links                           │   │
│  │   - Dropdown menus                             │   │
│  │   - User menu                                  │   │
│  └────────────────────────────────────────────────┘   │
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │ Discourse Content                              │   │
│  │ (Standard Discourse header hidden)             │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 1: Django Side (Already Complete ✅)

The following files have been created:

1. **`web/website/views/header_only.py`** - View that renders just the header
2. **`web/templates/website/header_only.html`** - Minimal template for iframe embedding
3. **`web/website/urls.py`** - Route added: `/header-only/`

**Test the endpoint:**
```bash
# After reloading Django
curl https://gel.monster/header-only/
```

You should see a minimal HTML page with just the navbar.

---

### Step 2: Discourse Theme Component

Create a new theme component in Discourse:

#### A. Create Theme Component

1. Go to **Admin → Customize → Themes**
2. Click **"Install"** → **"Create new"**
3. Name: `Django Header Integration`
4. Click **"Create"**

#### B. Add HTML (`</head>` section)

In the theme component, go to **Edit CSS/HTML** → **`</head>`** and add:

```html
<div id="gel-django-header-container"></div>
```

#### C. Add CSS (Common → CSS)

```css
/* Hide standard Discourse header */
.d-header {
  display: none !important;
}

/* Container for Django header iframe */
#gel-django-header-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 1031;
  background-color: #1a1d20; /* Match Django navbar background */
}

/* Iframe styling - seamless integration */
#gel-django-header-iframe {
  width: 100%;
  height: 80px; /* Initial height, will be adjusted dynamically */
  border: none;
  display: block;
  margin: 0;
  padding: 0;
  background: transparent;
  overflow: hidden;
}

/* Adjust Discourse content for fixed header */
#main-outlet {
  margin-top: 80px !important;
  padding-top: 20px;
}

body {
  padding-top: 80px;
}

.sidebar-wrapper {
  top: 80px !important;
}

/* Hide Discourse footer */
.about-footer {
  display: none !important;
}

/* Loading state */
#gel-django-header-container.loading::before {
  content: 'Loading header...';
  display: block;
  text-align: center;
  padding: 20px;
  color: rgba(255,255,255,0.5);
  font-size: 14px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  body, #main-outlet {
    padding-top: 60px;
    margin-top: 60px !important;
  }
  
  .sidebar-wrapper {
    top: 60px !important;
  }
}
```

#### D. Add JavaScript

In **Common → JavaScript** section:

```javascript
import { apiInitializer } from "discourse/lib/api";

export default apiInitializer("1.8.0", (api) => {
  let iframeLoaded = false;
  
  function createHeaderIframe() {
    const container = document.getElementById('gel-django-header-container');
    if (!container || iframeLoaded) return;
    
    // Mark container as loading
    container.classList.add('loading');
    
    // Create iframe
    const iframe = document.createElement('iframe');
    iframe.id = 'gel-django-header-iframe';
    iframe.src = 'https://gel.monster/header-only/';
    iframe.frameBorder = '0';
    iframe.scrolling = 'no';
    iframe.title = 'Gelatinous Monster Navigation';
    
    // Remove loading state when iframe loads
    iframe.onload = function() {
      container.classList.remove('loading');
      iframeLoaded = true;
    };
    
    // Add iframe to container
    container.appendChild(iframe);
  }
  
  // Listen for height updates from Django header iframe
  window.addEventListener('message', (event) => {
    // Verify origin for security
    if (event.origin !== 'https://gel.monster') return;
    
    if (event.data.type === 'gel-header-height') {
      const iframe = document.getElementById('gel-django-header-iframe');
      const height = event.data.height;
      
      if (iframe) {
        iframe.style.height = height + 'px';
        document.body.style.paddingTop = height + 'px';
        
        const mainOutlet = document.getElementById('main-outlet');
        if (mainOutlet) {
          mainOutlet.style.marginTop = height + 'px';
        }
        
        const sidebar = document.querySelector('.sidebar-wrapper');
        if (sidebar) {
          sidebar.style.top = height + 'px';
        }
      }
    }
  });
  
  // Create iframe on page change
  api.onPageChange(() => {
    if (!iframeLoaded) {
      createHeaderIframe();
    }
  });
  
  // Initial load
  createHeaderIframe();
  
  // Handle logout hash
  if (window.location.hash === '#logout') {
    document.cookie = '_forum_session=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.cookie = '_t=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    window.location.href = 'https://gel.monster/';
  }
});
```

---

### Step 3: Enable Theme Component

1. Click **"Save"** on your theme component
2. Go back to **Themes**
3. Edit your main theme (Foundation or whatever you're using)
4. Under **"Include component on these themes"**, add `Django Header Integration`
5. Save

---

## Testing Checklist

### Basic Functionality
- [ ] Header appears on forum homepage
- [ ] Header appears on topic pages
- [ ] Header appears on user profile pages
- [ ] No visual "seam" between header and content

### Authentication State
- [ ] When logged out of Django, header shows "Login/Register" links
- [ ] When logged in to Django, header shows user menu
- [ ] User dropdown works (clicks register correctly)
- [ ] Forum link highlights properly

### Navigation
- [ ] "Home" link goes to gel.monster
- [ ] "Help" link goes to gel.monster/help
- [ ] "Forum" link stays on forum (or refreshes)
- [ ] All links open in same tab (not new window)

### Responsive Behavior
- [ ] Header adjusts height when dropdowns open
- [ ] Mobile view hides navigation links appropriately
- [ ] No horizontal scrolling
- [ ] Touch interactions work on mobile

### Performance
- [ ] Header loads within 1 second
- [ ] No visible "flash" when loading
- [ ] Smooth scrolling behavior
- [ ] No layout shift after header loads

---

## Security Considerations

### Cross-Origin Communication

The implementation uses `postMessage` for iframe height communication:

```javascript
// In Django header (header_only.html)
window.parent.postMessage({
  type: 'gel-header-height',
  height: height
}, '*');

// In Discourse theme
window.addEventListener('message', (event) => {
  // ✅ VERIFY ORIGIN
  if (event.origin !== 'https://gel.monster') return;
  
  if (event.data.type === 'gel-header-height') {
    // Process height update
  }
});
```

**Security measures:**
- ✅ Origin verification on message receipt
- ✅ Specific message type checking
- ✅ No sensitive data transmitted
- ✅ Iframe sandbox not needed (same organization)

### Cookie Sharing

Cookies work correctly because:
- Django header iframe loads from `gel.monster` (same domain as main site)
- Discourse at `forum.gel.monster` is subdomain (cookies can be shared if configured)
- SSO already handles authentication sync

---

## Troubleshooting

### Header Not Appearing

**Symptom**: Blank space where header should be

**Fixes**:
1. Check browser console for errors
2. Verify `/header-only/` endpoint works: `curl https://gel.monster/header-only/`
3. Check iframe `src` URL in Discourse theme
4. Verify theme component is enabled on active theme

### Header Too Short/Tall

**Symptom**: Content overlaps or large gap

**Fixes**:
1. Check if `postMessage` height updates are working (browser console)
2. Verify JavaScript listener is active
3. Manually adjust initial height in CSS if needed

### Dropdown Menus Don't Work

**Symptom**: Clicking user menu does nothing

**Fixes**:
1. Check if Bootstrap JS is loading in iframe
2. Verify jQuery is loaded before Bootstrap
3. Check browser console for jQuery/Bootstrap errors
4. Test `/header-only/` endpoint directly in browser

### Mobile Issues

**Symptom**: Header overlaps content on mobile

**Fixes**:
1. Check media query breakpoints match Django
2. Verify mobile padding adjustments in CSS
3. Test on actual device (not just browser dev tools)

---

## Maintenance

### Updating Header

When you update Django's `_menu.html`:
1. Changes automatically apply to both sites
2. No Discourse theme updates needed
3. Users may need to hard refresh (Ctrl+F5) to clear cache

### Django Deployment

After deploying Django changes:
```bash
# Reload Django server
sudo systemctl reload evennia

# Clear Cloudflare cache if using CDN
# (Future when migrated to Cloudflare)
```

### Performance Monitoring

Monitor header load time:
```javascript
// In browser console on forum.gel.monster
performance.getEntriesByType('resource')
  .filter(r => r.name.includes('header-only'))
  .forEach(r => console.log('Header load time:', r.duration + 'ms'));
```

Target: < 500ms

---

## Future Enhancements

### Phase 2: Cloudflare Migration

When migrating to Cloudflare Tunnel (from Lightsail load balancers):

```javascript
// Cloudflare Worker can inject header server-side
export default {
  async fetch(request) {
    // Fetch Discourse response
    const response = await fetch(request);
    
    // Fetch Django header
    const header = await fetch('https://gel.monster/header-only/');
    
    // Inject header into HTML
    return new HTMLRewriter()
      .on('body', {
        element(element) {
          element.prepend(header.text(), {html: true});
        }
      })
      .transform(response);
  }
}
```

This eliminates the iframe entirely but requires Cloudflare Workers.

### Phase 3: Service Worker Caching

Cache header in browser service worker for instant load:

```javascript
// service-worker.js
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/header-only/')) {
    event.respondWith(
      caches.match(event.request).then(response => {
        return response || fetch(event.request);
      })
    );
  }
});
```

---

## Success Metrics

### Technical
- ✅ Header load time < 500ms
- ✅ Zero console errors
- ✅ 100% visual match with gel.monster
- ✅ All interactive elements functional

### User Experience
- ✅ Users don't notice it's an iframe
- ✅ Navigation feels seamless
- ✅ Authentication state accurate
- ✅ Mobile experience smooth

### Maintenance
- ✅ Single header codebase
- ✅ Changes propagate automatically
- ✅ No manual synchronization needed
- ✅ Easy to debug and update

---

## Rollback Plan

If issues arise:

1. **Disable theme component** in Discourse admin (instant rollback)
2. **Remove URL route** from Django urls.py
3. **Revert to previous approach** (custom CSS header)

Rollback time: < 5 minutes

---

## Conclusion

This iframe approach provides:
- ✅ 100% visual consistency between sites
- ✅ Single source of truth for header
- ✅ Full Django functionality preserved
- ✅ Easy maintenance
- ✅ Imperceptible to users

**Total Implementation Time**: ~30 minutes  
**Maintenance Overhead**: Near zero

The iframe method is the optimal solution for your Lightsail infrastructure and provides the best balance of simplicity, maintainability, and user experience.
