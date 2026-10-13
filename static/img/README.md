# PortaTap assets

These files are served directly. There is no separate icon source folder: this
directory is the single source of truth for the mark, the favicon, and the
installable app icons.

## Files

| File | What it is |
| --- | --- |
| `portatab-symbol.svg` | Primary cobalt symbol for light surfaces. |
| `portatab-symbol-white.svg` | White symbol, for the cobalt CTA block and any dark fill. |
| `portatab-app-icon.svg` | White symbol on the cobalt app tile. |
| `favicon.svg` | Browser icon, same tile as the app icon. |
| `favicon.ico` | Multi-size browser icon: 48, 32, and 16 px frames. |
| `apple-touch-icon.png` | iOS home screen icon (180 px, baked in). |
| `icon-192.png`, `icon-512.png` | PWA install icons. |
| `maskable-512.png` | PWA maskable icon, safe-zone padded. |
| `site.webmanifest` | Web app manifest pointing at the icons above. |
| `app-kasir.png` | Capture of the Order &amp; Kasir screen, used as the product shot on the landing page. |

## Brand values

- Primary blue: `#0068F9`
- Ink: `#121722`

## Usage

- Transparent symbol on light surfaces, app icon on its cobalt tile.
- Clear space around the symbol: at least the width of the handle dot.
- Do not stretch, rotate, add effects, or recolor the symbol.
- Regenerate `favicon.ico` and the PNG icons from `portatab-app-icon.svg` rather
  than editing the raster files by hand.

## Markup

Both base templates (`templates/base.html` and
`apps/website/templates/website/_site_base.html`) carry the same block:

```html
<link rel="icon" href="{% static 'img/favicon.ico' %}" sizes="48x48">
<link rel="icon" href="{% static 'img/favicon.svg' %}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{% static 'img/apple-touch-icon.png' %}">
<link rel="manifest" href="{% static 'img/site.webmanifest' %}">
<meta name="theme-color" content="#0068F9">
```

## Two blues

`--color-electric-cobalt` in `static/css/input.css` is `#2f6bff`, while the brand
value (and the `theme-color` meta, and the app icon tile) is `#0068F9`. The
interface accent and the installed-app chrome are therefore slightly different
blues. Aligning them means changing one token.

Trademark availability of the mark has not been checked.
