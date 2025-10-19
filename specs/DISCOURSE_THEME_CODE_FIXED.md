# Discourse Theme Component Code - FIXED
## Ready to Copy/Paste

Use this code in your Discourse theme component named "Django Header Integration"

---

## Step 1: HTML Code (Paste in `</head>` section)

```html
<div id="gel-django-header-container"></div>
```

---

## Step 2: CSS Code (Paste in Common → CSS)

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
  background-color: #1a1d20;
}

/* Iframe styling - seamless integration */
#gel-django-header-iframe {
  width: 100%;
  height: 80px;
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

---

## Step 3: JavaScript Code (Paste in Common → JavaScript)

**FIXED VERSION - Prevents double iframe creation**

```javascript
import { apiInitializer } from "discourse/lib/api";

export default apiInitializer("1.8.0", (api) => {
  let iframeCreated = false;
  
  function createHeaderIframe() {
    // Prevent multiple iframes - check if already created
    if (iframeCreated) return;
    
    const container = document.getElementById('gel-django-header-container');
    if (!container) return;
    
    // Check if iframe already exists in DOM
    const existingIframe = document.getElementById('gel-django-header-iframe');
    if (existingIframe) {
      iframeCreated = true;
      return;
    }
    
    // Mark as created immediately to prevent race conditions
    iframeCreated = true;
    
    container.classList.add('loading');
    
    const iframe = document.createElement('iframe');
    iframe.id = 'gel-django-header-iframe';
    iframe.src = 'https://gel.monster/header-only/';
    iframe.frameBorder = '0';
    iframe.scrolling = 'no';
    iframe.title = 'Gelatinous Monster Navigation';
    
    iframe.onload = function() {
      container.classList.remove('loading');
    };
    
    container.appendChild(iframe);
  }
  
  // Handle height updates from Django header iframe
  window.addEventListener('message', (event) => {
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
  
  // Create header on initial load and page changes
  // onPageChange fires on initial load, so no need for separate call
  api.onPageChange(() => {
    createHeaderIframe();
  });
  
  // Handle logout redirect
  if (window.location.hash === '#logout') {
    document.cookie = '_forum_session=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.cookie = '_t=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    window.location.href = 'https://gel.monster/';
  }
});
```

---

## Key Changes in Fixed Version

1. **Renamed flag**: `iframeLoaded` → `iframeCreated` (more accurate)
2. **Set flag immediately**: Prevents race condition by marking created before DOM insertion
3. **Check existing iframe**: Verify iframe doesn't already exist in DOM
4. **Removed duplicate call**: No longer calling `createHeaderIframe()` twice
5. **Added comments**: Clarified that `onPageChange` handles initial load

---

## Implementation Steps

1. **Go to Discourse Admin** → Customize → Themes
2. **Find your theme component**: "Django Header Integration"
3. **Edit CSS/HTML**
4. **Replace the JavaScript** with the fixed version above
5. **Save**
6. **Hard refresh your browser** (Cmd+Shift+R or Ctrl+Shift+R)
7. **Test** - you should now see only ONE header

---

## Troubleshooting

If you still see double headers after the fix:

1. **Clear browser cache completely**
2. **Open browser inspector** (F12) → Console tab
3. **Look for errors** related to iframe creation
4. **Check Elements tab** → Search for `gel-django-header-iframe`
5. **Verify only ONE iframe exists** with that ID

If you see TWO iframes with the same ID, the old JavaScript is still cached.
