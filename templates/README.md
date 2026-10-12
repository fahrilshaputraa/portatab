# Template structure — PortaTap

PortaTap uses **Django Templates + HTMX**. Templates are organised by domain so a
feature's markup lives next to the app that owns it.

## Two layers

| Location | Holds | Why |
| --- | --- | --- |
| `templates/` | Root layout, shared partials, reusable components, email templates, customer-facing menu pages | Cross-domain markup used by more than one app |
| `apps/<app>/templates/<app>/` | Domain templates for that app | Keeps a feature's views/forms/services/templates together (see AGENTS.md §4) |

Templates in `apps/*` are **namespaced** (`apps/catalog/templates/catalog/...`) so
`{% include %}` paths never collide between apps.

## Conventions

- `base.html` — root HTML document (nav, messages, blocks). Domain pages extend it.
- Every app has its own shell that extends the root, e.g. `tenants/base_dashboard.html`.
- Fragment partials (HTMX swap targets) are prefixed with `_`, e.g. `_order_row.html`,
  `_product_table.html`. Full pages are not.
- Reusable, parameterless-ish UI atoms live in `templates/components/` and are pulled in
  with `{% include %}` + `{% with %}`.
- Shared page furniture (pagination, messages) lives in `templates/partials/`.
- `templates/menu/` is the public customer QR surface (menu, cart, checkout, order
  tracking). It is a portal, not a domain, so it spans catalog + tables + orders.

## Layout

```
templates/
  base.html                 # root document shell
  components/               # reusable UI atoms (_button, _badge, _card, _empty_state)
  partials/                 # page furniture (_messages, _pagination, _form_errors)
  menu/                     # public customer QR portal
  emails/                   # transactional email bodies
apps/<app>/templates/<app>/
  ...                       # domain pages + `_`-prefixed HTMX fragments
```

## Naming rules

- `snake_case` filenames ending in `.html`.
- One concept per file; split a page into fragments instead of nesting deeply.
- Prefix fragments with `_` so it is obvious they are not routed standalone.

## Styling

Tailwind CSS (approved stack) compiles to `static/css/app.css`. Design tokens come from
`DESIGN.md` (cream canvas `#faf9f7`, electric cobalt `#0068f9`, Roobert/Inter type scale).
HTMX is the default for server-driven interactions; vanilla JS only for local browser
behaviour.
