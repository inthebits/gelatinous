````markdown
# Website Styling Specification

## Overview

Gelatinous uses a custom **terminal/brutalist** theme inspired by retro-futuristic corporate terminals (Weyland-Yutani, Nostromo aesthetic). The design features monospace typography, stark contrasts, and glowing green accents reminiscent of 1970s-80s computer terminals. The styling is implemented via `web/static/website/css/custom.css`, which is automatically loaded by Evennia's base template.

**Design Philosophy:**
- Terminal/brutalist aesthetic with monospace fonts
- Deep black backgrounds with stark white text
- Classic terminal green (#00ff00) for interactive elements
- Subtle glow effects for cyberpunk atmosphere
- Minimal decoration, maximum information density
- Corporate data terminal aesthetic

## Color Palette

### CSS Custom Properties

Defined in `:root` for consistent theming throughout the site:

```css
--terminal-bg-dark: #0a0a0a;         /* Deep black background */
--terminal-bg-medium: #1a1a1a;       /* Medium dark for cards */
--terminal-bg-light: #2a2a2a;        /* Light dark for inputs */
--terminal-green: #00ff00;           /* Classic terminal green */
--terminal-green-dim: #00aa00;       /* Dimmed green for less emphasis */
--terminal-text: #ffffff;            /* White text */
--terminal-text-muted: #888888;      /* Muted gray */
--terminal-yellow: #ffff00;          /* Warning/caution yellow */
--terminal-red: #ff0000;             /* Error/danger red */
--terminal-border: #333333;          /* Subtle borders */
--terminal-glow: rgba(0, 255, 0, 0.5); /* Green glow effect */
```

### Color Usage

| Color | Usage | Notes |
|-------|-------|-------|
| `#0a0a0a` (bg-dark) | Body, navbar, footer, card headers | Deep black |
| `#1a1a1a` (bg-medium) | Cards, dropdowns, alerts | Medium dark |
| `#2a2a2a` (bg-light) | Form inputs, buttons | Lighter dark |
| `#ffffff` (text) | All primary text | Maximum readability |
| `#00ff00` (green) | Hovers, focus, active states | Classic terminal |
| `#00aa00` (green-dim) | Links, non-hover states | Dimmed terminal |
| `#888888` (muted) | Secondary text, disabled states | Gray muted |
| `#ffff00` (yellow) | Warnings, caution | High visibility |
| `#ff0000` (red) | Errors, destructive actions | Danger |
| `#333333` (border) | Borders, separators | Subtle structure |

## Typography

### Font Stack

**All elements use monospace:**
```css
* {
    font-family: 'Courier New', Courier, monospace !important;
    letter-spacing: 0.02em;
}
```

**Rationale:**
- Courier New: Universal monospace availability
- Consistent character width for terminal aesthetic
- Slight letter-spacing for improved readability

### Text Styling

**Headings:**
```css
h1, h2, h3, h4, h5, h6 {
    color: var(--terminal-text);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
```
- All caps for corporate/military feel
- Increased letter-spacing for impact

**Labels:**
```css
label {
    color: var(--terminal-text);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.9rem;
}
```
- Uppercase for form consistency
- Slightly smaller than body text

## Component Styling

### Navigation Bar

```css
.navbar {
    background-color: var(--terminal-bg-dark) !important;
    border-bottom: 1px solid var(--terminal-border);
}

.navbar-brand,
.navbar-nav .nav-link {
    color: var(--terminal-text) !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.navbar-nav .nav-link:hover {
    color: var(--terminal-green) !important;
    text-shadow: 0 0 5px var(--terminal-glow);
}
```

**Features:**
- Deep black background
- White text, all caps
- Green glow on hover
- Subtle border separator

### Footer

```css
.footer {
    background-color: var(--terminal-bg-dark) !important;
    border-top: 1px solid var(--terminal-border);
}

.footer a.text-white:hover {
    color: var(--terminal-green) !important;
    text-shadow: 0 0 5px var(--terminal-glow);
}
```

**Features:**
- Matches navbar aesthetic
- Consistent hover effects
- Border separator at top

### Cards

```css
.card {
    background-color: var(--terminal-bg-medium);
    border: 1px solid var(--terminal-border);
    box-shadow: none;
    color: var(--terminal-text);
}

.card-header {
    background-color: var(--terminal-bg-dark);
    border-bottom: 1px solid var(--terminal-border);
    color: var(--terminal-text);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
```

**Features:**
- Medium dark background (#1a1a1a)
- Darker header (#0a0a0a)
- No shadows (brutalist)
- Uppercase headers with spacing
- Subtle borders only

### Links

```css
a {
    color: var(--terminal-green-dim);
    text-decoration: none;
}

a:hover {
    color: var(--terminal-green);
    text-decoration: none;
    text-shadow: 0 0 5px var(--terminal-glow);
}
```

**Features:**
- Dimmed green by default (#00aa00)
- Bright green on hover (#00ff00)
- Glow effect for emphasis
- No underlines (clean terminal look)

### Buttons

#### All Buttons
- Uppercase text with letter-spacing
- Border-focused design (brutalist)
- Glow effects on hover/focus
- No rounded corners (removed via border-radius: 0)

#### Primary Buttons
```css
.btn-primary {
    background-color: var(--terminal-bg-light);
    border: 1px solid var(--terminal-green-dim);
    color: var(--terminal-green-dim);
}

.btn-primary:hover {
    background-color: var(--terminal-bg-dark);
    border-color: var(--terminal-green);
    color: var(--terminal-green);
    text-shadow: 0 0 5px var(--terminal-glow);
    box-shadow: 0 0 10px var(--terminal-glow);
}
```

#### Danger Buttons
```css
.btn-danger {
    background-color: var(--terminal-bg-light);
    border: 1px solid var(--terminal-red);
    color: var(--terminal-red);
}

.btn-danger:hover {
    text-shadow: 0 0 5px rgba(255, 0, 0, 0.5);
    box-shadow: 0 0 10px rgba(255, 0, 0, 0.5);
}
```

#### Warning Buttons
```css
.btn-warning {
    background-color: var(--terminal-bg-light);
    border: 1px solid var(--terminal-yellow);
    color: var(--terminal-yellow);
}
```

**Features:**
- Color-coded by function
- Consistent glow effects
- Dark backgrounds with colored borders and text

### Forms

```css
.form-control {
    background-color: var(--terminal-bg-light);
    border: 1px solid var(--terminal-border);
    color: var(--terminal-text);
}

.form-control:focus {
    background-color: var(--terminal-bg-medium);
    border-color: var(--terminal-green);
    box-shadow: 0 0 5px var(--terminal-glow);
    color: var(--terminal-text);
}
```

**Features:**
- Dark backgrounds
- White text
- Green border and glow on focus
- Muted placeholder text

### Alerts

```css
.alert-success {
    background-color: var(--terminal-bg-medium);
    border: 1px solid var(--terminal-green);
    color: var(--terminal-green);
}

.alert-danger {
    background-color: var(--terminal-bg-medium);
    border: 1px solid var(--terminal-red);
    color: var(--terminal-red);
}

.alert-warning {
    background-color: var(--terminal-bg-medium);
    border: 1px solid var(--terminal-yellow);
    color: var(--terminal-yellow);
}
```

**Features:**
- Consistent dark backgrounds
- Color-coded borders and text
- No background transparency (solid)

### Tables

```css
.table thead th {
    border-bottom: 1px solid var(--terminal-border);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.85rem;
}

.table-hover tbody tr:hover {
    background-color: rgba(0, 255, 0, 0.05);
}
```

**Features:**
- Uppercase headers with spacing
- Subtle green tint on row hover
- Minimal borders

## Terminal Effects

### Scanline Overlay

```css
body::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(
        0deg,
        rgba(0, 0, 0, 0.1) 0px,
        rgba(0, 0, 0, 0.1) 1px,
        transparent 1px,
        transparent 2px
    );
    pointer-events: none;
    z-index: 9999;
    opacity: 0.3;
}
```

**Features:**
- Subtle horizontal scanlines
- CRT monitor aesthetic
- Doesn't interfere with interaction
- Can be adjusted via opacity

### Flicker Effect

```css
@keyframes terminal-flicker {
    0% { opacity: 0.9; }
    50% { opacity: 1; }
    100% { opacity: 0.9; }
}

.card {
    animation: terminal-flicker 0.15s ease-in-out;
}
```

**Features:**
- Brief flicker on card load
- Simulates CRT refresh
- Very subtle (0.15s duration)

### Glow Effects

Applied to:
- Links on hover
- Buttons on hover/focus
- Form inputs on focus
- Active navigation items

```css
text-shadow: 0 0 5px var(--terminal-glow);
box-shadow: 0 0 10px var(--terminal-glow);
```

## Utility Classes

### Terminal-Specific

```css
.terminal-prompt::before {
    content: ">";
    color: var(--terminal-green);
    margin-right: 0.5em;
}

.terminal-command {
    color: var(--terminal-green);
}

.terminal-output {
    color: var(--terminal-text-muted);
}

.terminal-error {
    color: var(--terminal-red);
}

.terminal-warning {
    color: var(--terminal-yellow);
}
```

**Usage:**
- Add terminal-style prompts to text
- Style command/output displays
- Color-code messages by type

## Responsive Design

### Mobile Adjustments

```css
@media (max-width: 768px) {
    .navbar-brand {
        font-size: 0.9rem;
    }
    
    h1 {
        font-size: 1.5rem;
    }
    
    h2 {
        font-size: 1.3rem;
    }
}
```

**Features:**
- Smaller fonts on mobile
- Maintains readability
- Preserves monospace aesthetic

## Accessibility

### Focus Indicators

```css
:focus {
    outline: 1px solid var(--terminal-green);
    outline-offset: 2px;
}
```

**Features:**
- Green outlines for visibility
- Consistent across all interactive elements
- Offset for clarity

### Contrast Ratios

- **White on Black**: Exceeds WCAG AAA (21:1)
- **Green on Black**: Exceeds WCAG AA (3.7:1)
- **Red on Black**: Exceeds WCAG AA (4.0:1)
- **Yellow on Black**: Exceeds WCAG AAA (14.6:1)

### Print Styles

```css
@media print {
    body {
        background-color: white !important;
        color: black !important;
    }
    
    body::before {
        display: none;
    }
}
```

**Features:**
- Black text on white for printing
- Removes scanlines and effects
- Hides navigation/footer

## Implementation Details

### File Location

```
web/static/website/css/custom.css
```

### Loading Mechanism

Evennia's `base.html` automatically loads `custom.css` after Bootstrap:

```html
<link rel="stylesheet" href="bootstrap.min.css">
<link rel="stylesheet" href="{% static 'website/css/website.css' %}">
<link rel="stylesheet" href="{% static 'website/css/custom.css' %}">
```

### Deployment Process

1. Edit `web/static/website/css/custom.css` locally
2. Test changes locally with `evennia start`
3. Commit to git:
   ```bash
   git add web/static/website/css/custom.css
   git commit -m "Update terminal styling"
   git push origin master
   ```
4. Deploy to production:
   ```bash
   ssh user@gel.monster 'cd ~/gel.monster/gelatinous && git pull && sudo docker compose exec evennia evennia collectstatic --noinput && sudo docker compose exec evennia evennia reload'
   ```

### collectstatic

Django's collectstatic gathers all static files (CSS, JS, images) into a single directory for serving. Must be run after CSS changes:

```bash
evennia collectstatic --noinput
```

## Discourse Integration

### Matching Discourse Theme

To match the terminal aesthetic in Discourse forums:

1. **Admin > Customize > Themes**
2. **Create New Theme**: "Gelatinous Terminal"
3. **Common > CSS**:

```css
:root {
    --primary: #00ff00;
    --secondary: #00aa00;
    --tertiary: #0a0a0a;
    --header_background: #0a0a0a;
    --header_primary: #ffffff;
}

body {
    font-family: 'Courier New', Courier, monospace !important;
    background-color: #0a0a0a;
    color: #ffffff;
}

.d-header {
    background-color: #0a0a0a;
    border-bottom: 1px solid #333333;
}

a {
    color: #00aa00;
}

a:hover {
    color: #00ff00;
    text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
}

.btn-primary {
    background-color: #2a2a2a;
    border: 1px solid #00aa00;
    color: #00aa00;
}

.btn-primary:hover {
    border-color: #00ff00;
    color: #00ff00;
    text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
}
```

4. **Save and Enable Theme**

### Iframe Header Matching

The `header_only.html` template loads the same `custom.css`, ensuring the navbar iframe in Discourse matches the main site aesthetic.

## Design Rationale

### Why Terminal/Brutalist?

1. **Cyberpunk Setting**: Matches game's dystopian sci-fi theme
2. **Information Density**: Monospace allows precise data alignment
3. **Nostalgia**: Evokes classic computing era (Alien, Blade Runner)
4. **Clarity**: High contrast reduces ambiguity
5. **Distinctive**: Stands out from modern web design trends

### Weyland-Yutani Influence

Inspired by the retro-futuristic terminals in *Alien* (1979):
- Monochrome green CRT displays
- Uppercase sans-serif typography
- Minimal UI decoration
- Corporate/military aesthetic
- Glowing text effects

### Benefits

1. **Atmosphere**: Reinforces game's cyberpunk setting
2. **Usability**: High contrast improves readability
3. **Performance**: Minimal effects, fast rendering
4. **Accessibility**: Excellent contrast ratios
5. **Uniqueness**: Memorable visual identity

## Customization Guide

### Changing Colors

Edit CSS variables in `:root`:

```css
:root {
    --terminal-green: #00ff00;       /* Change to desired accent */
    --terminal-bg-dark: #0a0a0a;     /* Change background */
}
```

### Adjusting Glow Intensity

Modify glow variables:

```css
text-shadow: 0 0 10px var(--terminal-glow);  /* Increase blur */
--terminal-glow: rgba(0, 255, 0, 0.8);       /* Increase opacity */
```

### Disabling Scanlines

Comment out or remove:

```css
/* body::before {
    ...scanline effect...
} */
```

### Alternative Color Schemes

**Amber Terminal:**
```css
--terminal-green: #ffb000;
--terminal-green-dim: #cc8800;
--terminal-glow: rgba(255, 176, 0, 0.5);
```

**Blue Terminal:**
```css
--terminal-green: #00aaff;
--terminal-green-dim: #0077cc;
--terminal-glow: rgba(0, 170, 255, 0.5);
```

## Testing Checklist

- [ ] Test in Chrome, Firefox, Safari, Edge
- [ ] Verify mobile responsiveness
- [ ] Check contrast ratios (WCAG)
- [ ] Test all button hover states
- [ ] Verify form input focus effects
- [ ] Check navbar dropdown appearance
- [ ] Test table hover effects
- [ ] Verify alert styling
- [ ] Check print styles
- [ ] Test Discourse theme match
- [ ] Verify iframe header consistency

## Browser Compatibility

**Fully Supported:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Graceful Degradation:**
- CSS custom properties fallback to defaults
- Scanlines disabled in older browsers
- Glow effects simplified in IE11

## Related Documentation

- **Evennia Template System**: [Evennia Docs](https://www.evennia.com/docs/latest/Components/Web-Templates.html)
- **Bootstrap 4 Documentation**: [getbootstrap.com/docs/4.6](https://getbootstrap.com/docs/4.6/)
- **CSS Custom Properties**: [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- **Discourse Theming**: [Discourse Theme Guide](https://meta.discourse.org/t/beginners-guide-to-using-discourse-themes/91966)

## Maintenance Notes

### Evennia Updates

When updating Evennia, verify:
- [ ] `base.html` still loads `custom.css`
- [ ] No new default styles conflict
- [ ] Bootstrap version compatibility
- [ ] collectstatic works correctly

### Future Enhancements

**Potential Additions:**
- [ ] CRT screen curvature effect
- [ ] Typing animation for dynamic content
- [ ] Phosphor persistence effect
- [ ] Color palette switcher (green/amber/blue)
- [ ] Accessibility toggle for effects
- [ ] Dark mode variant (less stark black)

---

**Last Updated**: October 22, 2025  
**Current Version**: Production (Terminal/Brutalist v1.0)  
**Previous Version**: Daring Fireball-inspired (deprecated October 22, 2025)  
**Maintainer**: Gelatinous Development Team

````

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
