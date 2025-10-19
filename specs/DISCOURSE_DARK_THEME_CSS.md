# Discourse Complete Theme CSS
## Django Header Integration + Color Palette Theme

**IMPORTANT**: This CSS works in conjunction with the Discourse Color Palette defined in `DISCOURSE_COLOR_PALETTE.md`. Apply the color palette FIRST, then use this CSS for structural overrides.

Copy and paste this **ENTIRE CSS** into your Discourse theme component's **Common → CSS** section.

---

```css
/* ===== DJANGO HEADER IFRAME INTEGRATION ===== */

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
  background-color: #1a1a1a;
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
