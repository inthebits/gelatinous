# Website Styling Specification

## Overview

Gelatinous uses a custom dark theme inspired by Daring Fireball (daringfireball.net), featuring white text on blue-gray backgrounds. The styling is implemented via `web/static/website/css/custom.css`, which is automatically loaded by Evennia's base template.

**Design Philosophy:**
- Dark, comfortable reading experience
- High contrast white text on dark backgrounds
- Subtle blue accents for interactivity
- Consistent styling across all UI components

## Color Palette

### CSS Custom Properties

Defined in `:root` for consistent theming throughout the site:

```css
--df-bg-dark: #4a525a;           /* Dark blue-gray for navbar/footer */
--df-bg-medium: #6b747c;         /* Medium gray-blue for cards/content */
--df-bg-light: #f5f5f5;          /* Very light gray (currently unused) */
--df-text-primary: #ffffff;      /* White text */
--df-text-dark: #2c3e50;         /* Dark text for light backgrounds */
--df-text-muted: #95a5a6;        /* Muted text */
--df-accent: #6fa8dc;            /* Light blue accent for links/buttons */
--df-accent-hover: #5a8fc7;      /* Darker blue on hover */
--df-border: #dee2e6;            /* Light border color */
```

### Color Usage

| Color | Usage | Notes |
|-------|-------|-------|
| `#4a525a` (bg-dark) | Navbar, footer, card headers | Primary dark background |
| `#6b747c` (bg-medium) | Cards, dropdowns, form controls | Content background |
| `#ffffff` (text-primary) | All text | Maximum readability |
| `#6fa8dc` (accent) | Links, primary buttons | Interactive elements |
| `#5a8fc7` (accent-hover) | Hover states | Slightly darker for feedback |

## Component Styling

### Navigation Bar

```css
.navbar {
    background-color: var(--df-bg-dark) !important;
}

.navbar-brand,
.navbar-nav .nav-link {
    color: var(--df-text-primary) !important;
}

.navbar-nav .nav-link:hover {
    color: var(--df-accent) !important;
}

.navbar .dropdown-menu {
    background-color: var(--df-bg-medium);
}
```

**Features:**
- Dark blue-gray background (#4a525a)
- White text for brand and links
- Blue accent on hover
- Dropdown menus use medium background
- Seamless blend with page background (no borders)

### Footer

```css
.footer {
    background-color: var(--df-bg-dark) !important;
}

.footer .text-white {
    color: var(--df-text-primary) !important;
}

.footer a.text-white:hover {
    color: var(--df-accent) !important;
}
```

**Features:**
- Matches navbar color (#4a525a)
- White text throughout
- Blue accent on link hover
- No borders for seamless appearance

### Body & Layout

```css
body {
    background-color: var(--df-bg-dark) !important;
    color: var(--df-text-primary);
}

.main-content,
.container {
    background-color: transparent;
}
```

**Features:**
- Dark background for entire page
- White default text color
- Transparent containers to show page background

### Cards

```css
.card {
    background-color: var(--df-bg-medium);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    color: var(--df-text-primary);
}

.card-header {
    background-color: var(--df-bg-dark);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--df-text-primary);
}

.card-body {
    color: var(--df-text-primary);
    background-color: var(--df-bg-medium);
}
```

**Features:**
- Medium gray-blue background (#6b747c)
- Darker header (#4a525a)
- Subtle white borders and shadows
- Force white text on all nested elements

**Special Override:**
```css
/* Force all card content to be dark themed */
.card .card-body,
.card .card-body p,
.card .card-body div,
.card .card-body span,
.card ul,
.card ol,
.card li {
    background-color: transparent !important;
    color: var(--df-text-primary) !important;
}
```

### Links

```css
a {
    color: var(--df-accent);
    text-decoration: none;
}

a:hover {
    color: var(--df-accent-hover);
    text-decoration: underline;
}
```

**Features:**
- Light blue color (#6fa8dc)
- No underline by default
- Darker blue on hover with underline
- High contrast against dark backgrounds

### Buttons

#### Primary Buttons
```css
.btn-primary {
    background-color: var(--df-accent);
    border-color: var(--df-accent);
    color: var(--df-text-primary);
}

.btn-primary:hover,
.btn-primary:focus {
    background-color: var(--df-accent-hover);
    border-color: var(--df-accent-hover);
}
```

**Features:**
- Blue accent background
- White text
- Darker on hover/focus

#### Secondary Buttons
```css
.btn-secondary {
    background-color: var(--df-bg-medium);
    border-color: var(--df-bg-medium);
    color: var(--df-text-primary);
}

.btn-secondary:hover,
.btn-secondary:focus {
    background-color: var(--df-bg-dark);
    border-color: var(--df-bg-dark);
}
```

**Features:**
- Medium gray background
- White text
- Darker on hover/focus

### Forms

```css
.form-control {
    background-color: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
    color: var(--df-text-primary);
}

.form-control:focus {
    background-color: rgba(255, 255, 255, 0.15);
    border-color: var(--df-accent);
    box-shadow: 0 0 0 0.2rem rgba(111, 168, 220, 0.25);
}

.form-control::placeholder {
    color: rgba(255, 255, 255, 0.5);
}
```

**Features:**
- Semi-transparent white backgrounds
- White text
- Blue border and glow on focus
- Dimmed placeholder text
- Labels use white with medium font-weight

### Alerts

```css
.alert-info {
    background-color: rgba(111, 168, 220, 0.2);
    border-color: var(--df-accent);
    color: var(--df-text-primary);
}

.alert-danger {
    background-color: rgba(220, 53, 69, 0.2);
    border-color: #dc3545;
    color: #ff6b7a;
}

.alert-success {
    background-color: rgba(40, 167, 69, 0.2);
    border-color: #28a745;
    color: #6adb8a;
}

.alert-warning {
    background-color: rgba(255, 193, 7, 0.2);
    border-color: #ffc107;
    color: #ffd54f;
}
```

**Features:**
- Semi-transparent colored backgrounds
- Colored borders matching alert type
- Lightened text colors for readability on dark

### Tables

```css
.table {
    color: var(--df-text-primary);
}

.table thead th {
    border-bottom: 2px solid rgba(255, 255, 255, 0.2);
    color: var(--df-text-primary);
    font-weight: 600;
}

.table td,
.table th {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.table-hover tbody tr:hover {
    background-color: rgba(111, 168, 220, 0.2);
}
```

**Features:**
- White text throughout
- Subtle white borders
- Bold headers with thicker bottom border
- Blue-tinted hover effect

### Pagination

```css
.pagination .page-link {
    background-color: var(--df-bg-medium);
    color: var(--df-text-primary);
    border-color: rgba(255, 255, 255, 0.2);
}

.pagination .page-link:hover {
    color: var(--df-accent);
    background-color: var(--df-bg-dark);
    border-color: var(--df-accent);
}

.pagination .page-item.active .page-link {
    background-color: var(--df-accent);
    border-color: var(--df-accent);
}

.pagination .page-item.disabled .page-link {
    background-color: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.3);
}
```

**Features:**
- Medium background for inactive pages
- Blue background for active page
- Hover shows blue accent
- Dimmed disabled pages

### Breadcrumbs

```css
.breadcrumb {
    background-color: var(--df-bg-medium);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.breadcrumb-item a {
    color: var(--df-accent);
}

.breadcrumb-item.active {
    color: rgba(255, 255, 255, 0.7);
}

.breadcrumb-item + .breadcrumb-item::before {
    color: rgba(255, 255, 255, 0.5);
}
```

**Features:**
- Medium gray background
- Blue links for clickable items
- Dimmed active item and separators

### Code Blocks

```css
code {
    color: var(--df-accent);
    background-color: rgba(0, 0, 0, 0.3);
    padding: 2px 4px;
    border-radius: 3px;
}

pre {
    background-color: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    padding: 10px;
    color: var(--df-text-primary);
}
```

**Features:**
- Inline code in blue accent color
- Dark semi-transparent backgrounds
- White text in pre blocks
- Subtle borders and rounded corners

### Text Utilities

```css
.text-muted {
    color: rgba(255, 255, 255, 0.6) !important;
}

.text-dark {
    color: var(--df-text-primary) !important;
}
```

**Features:**
- Muted text at 60% opacity
- Force white text on `.text-dark` override

### Horizontal Rules

```css
hr {
    border-top: 1px solid rgba(255, 255, 255, 0.2);
}
```

**Features:**
- Subtle white separator lines

## Responsive Design

### Mobile Adjustments

```css
@media (max-width: 768px) {
    .navbar-brand {
        font-size: 1rem;
    }
    
    .card {
        margin-bottom: 1rem;
    }
}
```

**Features:**
- Smaller navbar brand text on mobile
- Consistent card spacing

## Implementation Details

### File Location

```
web/static/website/css/custom.css
```

### Loading Mechanism

Evennia's `base.html` automatically loads `custom.css` after the base website styles:

```html
<!-- From evennia/web/templates/website/base.html -->
<link rel="stylesheet" type="text/css" href="{% static "website/css/website.css" %}">
<!-- Custom CSS -->
<link rel="stylesheet" type="text/css" href="{% static "website/css/custom.css" %}">
```

### Deployment Process

1. Edit `web/static/website/css/custom.css` locally
2. Test changes locally
3. Deploy to production via scp:
   ```bash
   scp web/static/website/css/custom.css user@gel.monster:/path/to/gelatinous/web/static/website/css/
   ```
4. Run Django's collectstatic:
   ```bash
   evennia collectstatic --noinput
   ```
5. Reload server to apply changes:
   ```bash
   evennia reload
   ```

### Override Strategy

All styles use `!important` sparingly, primarily for:
- Body and container backgrounds
- Navbar and footer colors
- Card content text color (to override Bootstrap defaults)

This ensures the dark theme takes precedence over Bootstrap's defaults while maintaining CSS specificity best practices.

## Design Rationale

### Why Daring Fireball?

Daring Fireball's design is known for:
- **Readability**: High contrast, comfortable for long reading sessions
- **Simplicity**: Clean, minimal design without distractions
- **Professionalism**: Mature aesthetic suitable for serious content

### Dark Theme Benefits

1. **Reduced Eye Strain**: Especially in low-light environments
2. **Focus**: Dark backgrounds make content stand out
3. **Modern Aesthetic**: Aligns with contemporary web design trends
4. **Power Efficiency**: Lower power consumption on OLED screens

### Accessibility Considerations

- **Contrast Ratio**: White (#ffffff) on dark blue-gray (#4a525a) exceeds WCAG AAA standards
- **Link Visibility**: Blue accent (#6fa8dc) clearly distinguishable from regular text
- **Hover States**: All interactive elements have clear hover feedback
- **Focus Indicators**: Form controls show blue glow on focus

## Customization Guide

### Changing the Color Scheme

To modify the color palette, edit the CSS custom properties in `:root`:

```css
:root {
    --df-bg-dark: #your-color;       /* Navbar, footer, card headers */
    --df-bg-medium: #your-color;     /* Cards, dropdowns */
    --df-text-primary: #your-color;  /* All text */
    --df-accent: #your-color;        /* Links, buttons */
    --df-accent-hover: #your-color;  /* Hover states */
}
```

### Adding New Component Styles

Follow the established pattern:
1. Use CSS custom properties for colors
2. Maintain consistent spacing (Bootstrap's spacing utilities)
3. Ensure white text by default
4. Add subtle borders with `rgba(255, 255, 255, 0.1)`
5. Use blue accent for interactive elements

### Testing Changes

1. **Browser DevTools**: Test color combinations for contrast
2. **Multiple Browsers**: Verify appearance in Chrome, Firefox, Safari
3. **Mobile Devices**: Check responsive behavior
4. **Light/Dark Mode**: Ensure styling works regardless of OS theme

## Maintenance Notes

### Bootstrap Version

Gelatinous uses Bootstrap 5 (bundled with Evennia). Custom styles override Bootstrap defaults where necessary using specificity and `!important` flags.

### Evennia Updates

When updating Evennia, verify that:
- `base.html` still loads `custom.css`
- No new default styles conflict with custom theme
- All overrides still apply correctly

### Browser Compatibility

Tested and working in:
- Chrome 118+
- Firefox 119+
- Safari 17+
- Edge 118+

CSS custom properties (CSS variables) are supported in all modern browsers.

## Related Documentation

- **Evennia Template System**: [Evennia Docs - Web Templates](https://www.evennia.com/docs/latest/Components/Web-Templates.html)
- **Bootstrap 5 Documentation**: [getbootstrap.com](https://getbootstrap.com/docs/5.0/getting-started/introduction/)
- **CSS Custom Properties**: [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)

---

**Last Updated**: October 17, 2025  
**Current Version**: Production (deployed to gel.monster)  
**Maintainer**: Gelatinous Development Team
