# Discourse Complete Theme CSS
## Django Header Integration + Color Palette Theme

**IMPORTANT**: This CSS works in conjunction with the Discourse Color Palette defined in `DISCOURSE_COLOR_PALETTE.md`. Apply the color palette FIRST, then use this CSS for structural overrides.

Copy and paste this **ENTIRE CSS** into your Discourse theme component's **Common → CSS** section.

---

```css
/* ===== DJANGO HEADER IFRAME INTEGRATION ===== */

/* Hide standard Discourse header - prevent flash */
.d-header {
  display: none !important;
}

/* Pre-allocate space to prevent layout shift */
body {
  padding-top: 80px;
}

#main-outlet {
  margin-top: 80px !important;
  padding-top: 20px;
}

/* Container for Django header iframe */
#gel-django-header-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  height: 80px; /* Fixed height prevents reflow */
  z-index: 1031;
  background-color: #1a1a1a;
  /* Optimize rendering */
  will-change: contents;
  contain: layout style;
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
  /* Performance optimizations */
  pointer-events: auto;
}

.sidebar-wrapper {
  top: 80px !important;
}

/* Hide Discourse footer */
.about-footer {
  display: none !important;
}

/* Simplified loading state - no jitter */
#gel-django-header-container.loading {
  background-color: #1a1a1a;
}

/* Mobile responsive - keep same height as desktop */
/* Django header handles its own mobile layout */
@media (max-width: 768px) {
  body {
    padding-top: 80px;
  }
  
  #main-outlet {
    margin-top: 80px !important;
  }
  
  #gel-django-header-container {
    height: 80px;
  }
  
  #gel-django-header-iframe {
    height: 80px;
  }
  
  .sidebar-wrapper {
    top: 80px !important;
  }
}
```

---

## Setup Order

**Step 1: Apply Color Palette**
1. Go to **Discourse Admin** → **Customize** → **Colors**
2. Create the color scheme from `DISCOURSE_COLOR_PALETTE.md`
3. Apply it to your theme

**Step 2: Apply This CSS**
1. Go to **Discourse Admin** → **Customize** → **Themes**
2. Edit your "Django Header Integration" theme component
3. Go to **Common → CSS**
4. Paste the CSS above (lines 9-71)
5. **Save**

**Step 3: Refresh**
- Hard refresh your browser (Cmd+Shift+R or Ctrl+Shift+R)

---

## What This CSS Does

Since the **Color Palette handles all theming**, this CSS only focuses on:

1. **Django Header Integration**:
   - Hides native Discourse header
   - Embeds Django header in iframe
   - Adjusts page spacing for fixed header
   - Mobile responsive adjustments

2. **Structural Overrides**:
   - Hides Discourse footer
   - Loading state for header iframe
   - No color definitions (handled by palette)

The color palette system is more reliable because:
- ✅ Discourse generates all CSS based on palette values
- ✅ Works across ALL pages including admin
- ✅ Handles dynamic content automatically
- ✅ Easier to maintain and update

---

## Note

**Colors are now managed through the Discourse Color Palette** - not CSS variables. This means:
- All color changes should be made in **Admin → Colors**
- This CSS file should only contain structural/layout overrides
- The palette and CSS work together for complete theming
