# Rogue Linux Website: SSG & Fragments

## 1. Overview
The Rogue Linux website is built using a custom **Static Site Generator (SSG)** script (`website/build_site.py`). This approach was chosen to ensure a "Cyberpunk" speed (76KB payload) and maximum security (no server-side dynamic execution).

## 2. Fragment-Based Architecture
Instead of full HTML pages in the source, we use **Page Fragments**.
- **Source Location**: `website/src/pages/`
- **Format**: Pure content fragments (no `<html>`, `<head>`, or `<body>` tags).
- **Benefit**: Content is decoupled from the layout, allowing global design changes without editing every page.

## 3. Component Partial System
Common UI elements are extracted into **Partials**.
- **Location**: `website/src/partials/`
- **Components**: `nav.html`, `footer.html`.
- **Injection**: The SSG injects these into a base template at build time.

## 4. SSG Build Logic (`build_site.py`)
1. **Template Parsing**: Reads the master base template.
2. **Partial Injection**: Replaces placeholders like `{{nav}}` with content from `src/partials/`.
3. **Content Merging**: Reads each fragment in `src/pages/`, injects it into the template, and writes the final `.html` to the root (or `public/`).
4. **Metadata Extraction**: Scrapes `<!-- title: ... -->` comments from fragments to dynamically set `<title>` tags.

## 5. Deployment
The site is purely static and can be served from any secure location (Nginx, S3, etc.) with zero dependencies.
