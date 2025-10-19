# Discourse Complete Theme CSS
## Django Header Integration + Dark Theme

Copy and paste this **ENTIRE CSS** into your Discourse theme component's **Common → CSS** section. This replaces all existing CSS.

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
  background-color: #4a525a;
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

/* ===== DARK THEME FOR DISCOURSE ===== */
/* ===== DARK THEME FOR DISCOURSE ===== */
/* Matches Django's Daring Fireball-inspired color scheme */

:root {
    --df-bg-dark: #4a525a;
    --df-bg-medium: #6b747c;
    --df-text-primary: #ffffff;
    --df-text-muted: #95a5a6;
    --df-accent: #6fa8dc;
    --df-accent-hover: #5a8fc7;
}

/* ===== MAIN BACKGROUND ===== */
body {
    background-color: var(--df-bg-dark) !important;
}

#main-outlet {
    background-color: var(--df-bg-dark) !important;
}

.full-width {
    background-color: var(--df-bg-dark) !important;
}

/* ===== TOPIC LIST ===== */
.topic-list {
    background-color: var(--df-bg-medium) !important;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.topic-list-item {
    background-color: var(--df-bg-medium) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.topic-list-item:hover {
    background-color: rgba(111, 168, 220, 0.2) !important;
}

.topic-list-item.visited {
    background-color: rgba(0, 0, 0, 0.2) !important;
}

.topic-list-item.visited:hover {
    background-color: rgba(111, 168, 220, 0.15) !important;
}

/* Topic list text colors */
.topic-list .link-top-line,
.topic-list .discourse-tag,
.topic-list-item .main-link .title,
.topic-list-item .topic-excerpt {
    color: var(--df-text-primary) !important;
}

.topic-list-item .topic-excerpt {
    color: rgba(255, 255, 255, 0.7) !important;
}

/* ===== CATEGORY BOXES ===== */
.category-boxes,
.category-boxes-with-topics {
    background-color: var(--df-bg-dark) !important;
}

.category-box,
.category-box-inner {
    background-color: var(--df-bg-medium) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.category-box:hover {
    background-color: rgba(111, 168, 220, 0.2) !important;
}

.category-box .category-name,
.category-box .category-description {
    color: var(--df-text-primary) !important;
}

/* ===== POSTS ===== */
.topic-post,
.topic-post article {
    background-color: var(--df-bg-medium) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.topic-body,
.topic-avatar,
.post-info {
    background-color: transparent !important;
}

.cooked,
.cooked p,
.cooked li,
.cooked h1,
.cooked h2,
.cooked h3,
.cooked h4,
.cooked h5,
.cooked h6 {
    color: var(--df-text-primary) !important;
}

/* ===== NAVIGATION ===== */
.navigation-topics {
    background-color: var(--df-bg-medium) !important;
}

.list-controls {
    background-color: var(--df-bg-medium) !important;
}

.nav-pills > li > a {
    color: var(--df-text-primary) !important;
}

.nav-pills > li.active > a,
.nav-pills > li > a:hover {
    background-color: var(--df-accent) !important;
    color: var(--df-text-primary) !important;
}

/* ===== BUTTONS ===== */
.btn,
.btn-primary,
.btn-default {
    background-color: var(--df-accent) !important;
    color: var(--df-text-primary) !important;
    border: 1px solid var(--df-accent) !important;
}

.btn:hover,
.btn-primary:hover,
.btn-default:hover {
    background-color: var(--df-accent-hover) !important;
    border-color: var(--df-accent-hover) !important;
}

.btn-flat {
    background-color: transparent !important;
    color: var(--df-accent) !important;
}

.btn-flat:hover {
    background-color: rgba(111, 168, 220, 0.2) !important;
}

/* ===== SIDEBAR ===== */
.sidebar-sections,
.sidebar-section-wrapper {
    background-color: var(--df-bg-medium) !important;
}

.sidebar-section-header-text,
.sidebar-section-link,
.sidebar-section-message {
    color: var(--df-text-primary) !important;
}

.sidebar-section-link:hover {
    background-color: rgba(111, 168, 220, 0.2) !important;
}

/* ===== SEARCH ===== */
.search-menu,
.search-menu .results {
    background-color: var(--df-bg-medium) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.search-menu .search-result-post,
.search-menu .search-result-topic {
    color: var(--df-text-primary) !important;
}

.search-input {
    background-color: rgba(255, 255, 255, 0.1) !important;
    color: var(--df-text-primary) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

/* ===== COMPOSER (NEW POST) ===== */
.d-editor-container,
.d-editor-preview-wrapper,
.d-editor-textarea-wrapper {
    background-color: var(--df-bg-medium) !important;
}

.d-editor-input,
.d-editor-preview {
    background-color: rgba(255, 255, 255, 0.1) !important;
    color: var(--df-text-primary) !important;
}

#reply-control {
    background-color: var(--df-bg-dark) !important;
    border-top: 2px solid rgba(255, 255, 255, 0.2) !important;
}

/* ===== MODALS / POPUPS ===== */
.modal,
.modal-inner-container {
    background-color: var(--df-bg-medium) !important;
}

.modal-header,
.modal-body,
.modal-footer {
    background-color: var(--df-bg-medium) !important;
    color: var(--df-text-primary) !important;
}

/* ===== LINKS ===== */
a {
    color: var(--df-accent) !important;
}

a:hover {
    color: var(--df-accent-hover) !important;
}

/* ===== BADGES & TAGS ===== */
.badge-notification,
.badge-group {
    background-color: var(--df-accent) !important;
    color: var(--df-text-primary) !important;
}

.discourse-tag,
.discourse-tags .discourse-tag {
    background-color: rgba(111, 168, 220, 0.3) !important;
    color: var(--df-text-primary) !important;
}

/* ===== USER MENU ===== */
.menu-panel,
.user-menu,
.quick-access-panel {
    background-color: var(--df-bg-medium) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.menu-panel li,
.quick-access-panel li {
    color: var(--df-text-primary) !important;
}

.menu-panel li:hover,
.quick-access-panel li:hover {
    background-color: rgba(111, 168, 220, 0.2) !important;
}

/* ===== TIMELINE ===== */
.topic-timeline {
    background-color: transparent !important;
}

.timeline-container,
.timeline-controls {
    color: var(--df-text-primary) !important;
}

/* ===== CODE BLOCKS ===== */
pre,
code {
    background-color: rgba(0, 0, 0, 0.3) !important;
    color: var(--df-text-primary) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* ===== TABLES ===== */
table {
    background-color: var(--df-bg-medium) !important;
}

table th,
table td {
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: var(--df-text-primary) !important;
}

/* ===== QUOTES ===== */
aside.quote {
    background-color: rgba(0, 0, 0, 0.3) !important;
    border-left: 5px solid var(--df-accent) !important;
}

aside.quote .title {
    color: var(--df-accent) !important;
}

/* ===== ADMIN CONTROLS ===== */
.admin-controls {
    background-color: var(--df-bg-medium) !important;
}

/* ===== PAGINATION ===== */
.paginated-topics-list {
    background-color: var(--df-bg-medium) !important;
}

/* ===== FOOTER ===== */
.about-footer {
    display: none !important; /* Already hidden in main CSS */
}

/* ===== TEXT SELECTION ===== */
::selection {
    background-color: var(--df-accent) !important;
    color: var(--df-text-primary) !important;
}

::-moz-selection {
    background-color: var(--df-accent) !important;
    color: var(--df-text-primary) !important;
}

/* ===== SCROLLBAR (Webkit) ===== */
::-webkit-scrollbar {
    width: 12px;
}

::-webkit-scrollbar-track {
    background-color: var(--df-bg-dark);
}

::-webkit-scrollbar-thumb {
    background-color: var(--df-bg-medium);
    border-radius: 6px;
}

::-webkit-scrollbar-thumb:hover {
    background-color: var(--df-accent);
}
```

---

## How to Apply

1. **Go to Discourse Admin** → Customize → Themes
2. **Find your theme component**: "Django Header Integration"
3. **Edit CSS/HTML** → Common → CSS
4. **Select ALL existing CSS and DELETE it**
5. **Paste this ENTIRE CSS file** (from line 9 to the end of the code block above)
6. **Save**
7. **Hard refresh** your browser (Cmd+Shift+R or Ctrl+Shift+R)

---

## What This Does

**Django Header Integration:**
- Hides native Discourse header
- Embeds Django header in iframe at top
- Adjusts spacing for fixed header
- Mobile responsive

**Dark Theme:**
- Dark blue-gray backgrounds matching Django (`#4a525a`, `#6b747c`)
- White text throughout
- Light blue accent colors for links and buttons (`#6fa8dc`)
- Consistent styling with your main site
- Covers all Discourse elements: posts, topics, sidebar, modals, search, etc.

The entire site will have a cohesive dark theme from the Django header through all Discourse content!

---

## Note

This CSS file contains:
1. **Lines 1-77**: Django header iframe integration (replaces native header)
2. **Lines 79-end**: Complete dark theme styling (all Discourse elements)

Both sections work together to create a seamless experience between Django and Discourse.
