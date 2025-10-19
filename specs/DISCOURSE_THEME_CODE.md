# Discourse Theme Component Code
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

```javascript
import { apiInitializer } from "discourse/lib/api";

export default apiInitializer("1.8.0", (api) => {
  let iframeLoaded = false;
  
  function createHeaderIframe() {
    const container = document.getElementById('gel-django-header-container');
    if (!container || iframeLoaded) return;
    
    container.classList.add('loading');
    
    const iframe = document.createElement('iframe');
    iframe.id = 'gel-django-header-iframe';
    iframe.src = 'https://gel.monster/header-only/';
    iframe.frameBorder = '0';
    iframe.scrolling = 'no';
    iframe.title = 'Gelatinous Monster Navigation';
    
    iframe.onload = function() {
      container.classList.remove('loading');
      iframeLoaded = true;
    };
    
    container.appendChild(iframe);
  }
  
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
  
  api.onPageChange(() => {
    if (!iframeLoaded) {
      createHeaderIframe();
    }
  });
  
  createHeaderIframe();
  
  if (window.location.hash === '#logout') {
    document.cookie = '_forum_session=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    document.cookie = '_t=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    window.location.href = 'https://gel.monster/';
  }
});
```

---

## Implementation Steps

1. **Go to Discourse Admin** → Customize → Themes
2. **Click "Install"** → "Create new"
3. **Name it**: `Django Header Integration`
4. **Click "Create"**
5. **Go to "Edit CSS/HTML"**
6. **Paste HTML** in `</head>` section (Step 1 above)
7. **Paste CSS** in Common → CSS (Step 2 above)
8. **Paste JavaScript** in Common → JavaScript (Step 3 above)
9. **Click "Save"**
10. **Go back to Themes** and edit your active theme (Foundation)
11. **Under "Include component on these themes"**, add `Django Header Integration`
12. **Save and test!**

Visit forum.gel.monster and you should see the Django header!
