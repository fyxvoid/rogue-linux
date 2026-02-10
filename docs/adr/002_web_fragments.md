# ADR 002: Fragment-based Web Architecture

## Context
Initial website prototypes duplicated the Navigation and Footer HTML across every page (`index.html`, `packages.html`, etc.). This made changing a link in the Navbar a nightmare, requiring updates to every single file.

## Decision
We adopted a **Fragment Architecture**.
1.  **Partials**: `head`, `nav`, `footer` are extracted to `website/src/partials/`.
2.  **Fragments**: Page files in `website/src/pages/` contain *only* the content unique to that page (no `<html>`, `<body>` tags).
3.  **Builder**: The SSG script (`build_site.py`) handles the injection of fragments into a standard layout template.

## Consequences
### Positive
-   **DRY (Don't Repeat Yourself)**: Navbar changes are applied globally instantly.
-   **Scalability**: Adding a new page is just adding a content fragment; the system handles the rest.
-   **SEO**: The builder ensures consistent `<title>` and `<meta>` tags.

### Negative
-   **Developer Experience**: You cannot open a fragment directly in a browser to preview it; you must run the build script first.

## Status
ACCEPTED
