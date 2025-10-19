# Discourse Color Palette Configuration
## Gel.Monster Dark Theme

Use these exact color values in your Discourse Color Scheme:

**Admin → Customize → Colors → Create/Edit Color Scheme**

---

## Color Values

### Main text and icons
**primary**: `#ffffff`
- White text for maximum readability on dark backgrounds

### Main background and some button text
**secondary**: `#1a1a1a`
- Very dark gray/black - main background color matching Django site navbar and body

### Accent color (links, buttons, badges)
**tertiary**: `#6fa8dc`
- Light blue accent color for links and buttons (matches your site)

### Optional theme accent
**quaternary**: `#3a3a3a`
- Lighter charcoal for hover states and secondary elements

### Header background
**header_background**: `#1a1a1a`
- Matches main background for seamless Django header integration

### Header text and icons
**header_primary**: `#ffffff`
- White text in header matching your Django navbar

### Active or selected items
**selected**: `#5a8fc7`
- Darker blue for selected/active states (your accent-hover color)

### Hover or focus background
**hover**: `#2a2a2a`
- Dark charcoal for hover backgrounds

### Highlighted posts or topics
**highlight**: `#6fa8dc`
- Light blue accent matching your links

### Errors and delete actions
**danger**: `#dc3545`
- Red for errors and destructive actions

### Successful actions
**success**: `#28a745`
- Green for success states

### Like button
**love**: `#6fa8dc`
- Light blue matching your accent color

### tertiary-med-or-tertiary
**tertiary-med-or-tertiary**: `#6fa8dc`
- Same as tertiary accent

---

## How to Apply

1. Go to **Discourse Admin** → **Customize** → **Colors**
2. Click **+ New** to create a new color scheme (or edit existing)
3. Name it: `Gel.Monster Dark`
4. Copy each color value above into the corresponding field
5. Click **Save**
6. Go to **Customize** → **Themes**
7. Edit your theme
8. Under **Color Schemes**, select `Gel.Monster Dark`
9. **Save** and refresh your browser

---

## Result

This color palette will:
- Set the main background to `#1a1a1a` (matching your Django site)
- Use white text throughout for readability
- Apply green (`#39845b`) for accent colors matching your branding
- Ensure consistent colors across ALL Discourse pages (including admin)
- Work with your existing CSS customizations

The Color Scheme approach is more reliable than pure CSS because Discourse uses these values throughout its generated styles.
