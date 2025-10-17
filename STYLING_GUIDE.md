# Evennia Website Styling Guide

## What Went Wrong

The previous styling attempt failed because we tried to extend `"evennia/base.html"` which **doesn't exist**. 

### The Mistake
```django
{% extends "evennia/base.html" %}  ❌ WRONG - This path doesn't exist
```

## How Evennia's Template System Actually Works

### Template Structure

Looking at the Evennia source code, all website templates extend `"website/base.html"`:

```html
<!-- From evennia/web/templates/website/login.html -->
{% extends "website/base.html" %}  ✅ CORRECT
```

### The Base Template Location

The actual base template is located at:
- `evennia/web/templates/website/base.html` (Evennia core)
- Can be overridden at: `mygame/web/templates/website/base.html`

### How Evennia Loads Templates

Django searches for templates in this order:
1. **First**: `mygame/web/templates/`
2. **Then**: `evennia/web/templates/`

So to override, you put files with the same name in `mygame/web/templates/`.

## The CORRECT Way to Add Custom CSS

According to Evennia documentation, there are **two proper methods**:

### Method 1: Use the Existing `custom.css` File (RECOMMENDED)

Evennia's `base.html` already loads a `custom.css` file:

```html
<!-- From evennia/web/templates/website/base.html lines 15-27 -->
<!-- Base CSS -->
<link rel="stylesheet" type="text/css" href="{% static "website/css/website.css" %}">

{% comment %}
Allows for loading custom styles without overriding the base site styles
{% endcomment %}
<!-- Custom CSS -->
<link rel="stylesheet" type="text/css" href="{% static "website/css/custom.css" %}">
```

**Steps:**
1. Create file: `web/static/website/css/custom.css`
2. Add your CSS styles there
3. Reload server

**Advantages:**
- No template modifications needed
- Evennia already looks for this file
- Easy to revert (just delete the file)
- Won't break on Evennia updates

### Method 2: Override `base.html` to Add Additional CSS (Advanced)

If you need more control, you can override the entire base template or just extend it.

**Option A: Extend using blocks**
```django
{% extends "website/base.html" %}  ✅ CORRECT PATH

{% block header_ext %}
  {{ block.super }}
  <link rel="stylesheet" type="text/css" href="{% static 'website/css/additional.css' %}">
{% endblock %}
```

**Option B: Copy and modify entire base.html**
1. Copy `evennia/web/templates/website/base.html`
2. Paste to `mygame/web/templates/website/base.html`
3. Modify as needed

## Available Blocks in `base.html`

From the Evennia source, these blocks can be overridden:

```html
{% block header_ext %}{% endblock %}        <!-- Extra header content -->
{% block titleblock %}{% endblock %}        <!-- Page title -->
{% block body %}{% endblock %}              <!-- Entire body -->
{% block sidebar %}{% endblock %}           <!-- Sidebar content -->
{% block content %}{% endblock %}           <!-- Main content area -->
{% block footer %}{% endblock %}            <!-- Footer -->
```

## Static Files System

### How Static Files Work

Django collects static files from multiple locations into one place:

1. **Evennia's static files**: `evennia/web/static/`
2. **Your static files**: `mygame/web/static/`
3. **Collected to**: `mygame/server/.static/` (auto-generated)

### Override Priority

If you put a file at `mygame/web/static/website/css/custom.css`, it will **override** any file at `evennia/web/static/website/css/custom.css`.

### Important Note About .gitignore

The `web/static/` directory is in `.gitignore` by default. To commit static files:

```bash
git add -f web/static/website/css/custom.css
```

### Applying Static File Changes

After adding/modifying static files:

```bash
# Manual collection (optional - reload does this automatically)
evennia collectstatic --no-input

# OR just reload server
evennia reload
```

Then clear browser cache (Ctrl+F5 in most browsers).

## Recommended Approach for Daring Fireball Styling

### Step 1: Create `custom.css`

```bash
mkdir -p web/static/website/css/
```

Create `web/static/website/css/custom.css` with your styles:

```css
/* Daring Fireball inspired color scheme */

:root {
    --df-bg-dark: #4a525a;
    --df-bg-medium: #6b747c;
    --df-bg-light: #f5f5f5;
    --df-text-primary: #ffffff;
    --df-text-dark: #2c3e50;
    --df-accent: #6fa8dc;
    --df-accent-hover: #5a8fc7;
}

/* Navbar */
.navbar {
    background-color: var(--df-bg-dark) !important;
}

/* Footer */
.footer {
    background-color: var(--df-bg-dark) !important;
}

/* Body background */
body {
    background-color: var(--df-bg-light) !important;
}

/* Cards */
.card {
    background-color: var(--df-text-primary);
    border: 1px solid #dee2e6;
}

/* Links */
a {
    color: var(--df-accent);
}

a:hover {
    color: var(--df-accent-hover);
}

/* Buttons */
.btn-primary {
    background-color: var(--df-accent);
    border-color: var(--df-accent);
}

.btn-primary:hover {
    background-color: var(--df-accent-hover);
    border-color: var(--df-accent-hover);
}
```

### Step 2: Git Add (forced because of .gitignore)

```bash
git add -f web/static/website/css/custom.css
git commit -m "feat: Add Daring Fireball color scheme to custom.css"
git push
```

### Step 3: Deploy

```bash
ssh -i ~/Documents/LightsailDefaultKey-us-west-2.pem ubuntu@play.gel.monster
cd gel.monster/gelatinous
git pull
sudo docker exec gelatinous-evennia-1 evennia reload
```

### Step 4: Test

Visit https://gel.monster and clear browser cache (Ctrl+F5).

## Why This Approach is Better

1. **No template modifications** - Uses Evennia's built-in `custom.css` support
2. **Won't break** - Template structure unchanged
3. **Easy to test** - Just delete `custom.css` to revert
4. **Follows documentation** - This is the official Evennia way
5. **Survives updates** - Won't conflict with Evennia version upgrades

## Evennia Documentation References

From `evennia/evennia` repo research:

- **Website docs**: `docs/source/Components/Website.md`
- **Styling section**: Lines 168-205
- **Base template**: `evennia/web/templates/website/base.html`
- **Custom CSS comment**: Lines 21-27 explicitly mention custom.css

### Key Quote from Docs

> "The website's custom CSS is found in `evennia/web/static/website/css/website.css` 
> but we also look for a (currently empty) `custom.css` in the same location. 
> You can override either, but it may be easier to revert your changes if you 
> only add things to `custom.css`."

## Example from Evennia Source

The REST API uses this exact pattern:

```html
<!-- From evennia/web/templates/rest_framework/api.html -->
{% extends "rest_framework/base.html" %}

{% block style %}
  {{ block.super }}
  <link rel="stylesheet" type="text/css" href="{% static 'rest_framework/css/api.css' %}">
{% endblock %}
```

Notice:
1. Extends the correct base path
2. Uses `{{ block.super }}` to keep parent styles
3. Adds custom CSS file

## Testing Locally (Optional)

If you want to test before deploying:

```bash
# In your local gelatinous directory
cd /Users/daiimus/Documents/Projects/Repositories/Evennia/gelatinous
evennia reload
# Visit http://localhost:4001
```

## Troubleshooting

### CSS Not Showing Up?

1. Clear browser cache (Ctrl+F5)
2. Check file was collected: `ls server/.static/website/css/custom.css`
3. View page source - look for `<link>` tag loading custom.css
4. Use browser dev tools (F12) to see if CSS file loads

### Template Errors?

If you do modify templates and get errors:

1. Check you extended the right base: `{% extends "website/base.html" %}`
2. Make sure you didn't break block structure
3. Check for typos in `{% ... %}` tags
4. Look at Evennia logs: `evennia --log`

### Static Files Not Updating?

```bash
# Force static file collection
evennia collectstatic --no-input --clear
evennia reload
```

## Next Steps

1. Create `custom.css` with Daring Fireball colors
2. Test locally first (optional)
3. Commit and deploy
4. Iterate on styling as needed

The key insight: **Don't modify templates for simple styling. Use custom.css.**
