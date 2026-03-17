# stabatmater-hugo

Proof-of-concept migration of [stabatmater.info](https://stabatmater.info) from WordPress to Hugo + GitHub Pages.

⚠️ **This is a TEST site.** The production website is at [stabatmater.info](https://stabatmater.info).
The site includes `robots.txt` and `noindex` meta tags so search engines do not index it.

**Live test site:** https://mrnspam.github.io/stm/

---

## Content structure

```
content/
  _index.md              ← home page (banner: banner-8.jpg)
  about.md
  contact.md
  missing-cds.md
  texts.md
  translations/
    _index.md
  blog/
    _index.md
    YYYY-MM-DD-title.md  ← one file per blog post
  composers/
    _index.md            ← composers section index
    firstname-lastname.md  ← one file per composer
    alphabetically.md    ← sorting view (is_index: true)
    by-country.md        ← sorting view (is_index: true)
    chronologically.md   ← sorting view (is_index: true)
    by-duration.md       ← sorting view (is_index: true)
```

---

## Adding or editing a composer

File: `content/composers/firstname-lastname.md`

```yaml
---
title: "Firstname Lastname"
born: 1710
died: 1736
country: "Italy"
period: "Baroque"   # Medieval / Renaissance / Baroque / Classical / Romantic / Modern / Contemporary
banner: "banner9.jpg"   # optional — inherits from composers/_index.md if omitted
---
```

Body is free-form Markdown (verbatim from the original WordPress page). Use `## About the composer` and `## About the Stabat Mater` as section headings. CD recording tables and colour bar images can be included as raw HTML.

> **Important:** `is_index: true` is reserved for the four sorting index pages. Do not add it to real composer pages.

### Sorting views (auto-generated)

The four Composers sub-pages are generated automatically from front matter:

| Page | URL | Sorted by |
|------|-----|-----------|
| Alphabetically | `/composers/` | Title A–Z (A–Z filter bar) |
| By country of origin | `/composers/by-country/` | `country` front matter, then title |
| Chronologically | `/composers/chronologically/` | `period` (fixed order), then `born` year |
| By duration | `/composers/by-duration/` | alphabetical list (colour bars show duration visually) |

---

## Adding a blog post

File: `content/blog/YYYY-MM-DD-short-title.md`

```yaml
---
title: "Full post title"
date: 2025-06-01
summary: "One sentence for the blog list and homepage."
---

Post body in English...
```

---

## Hero banners

Each page type uses a different hero banner image, controlled by `banner:` in front matter:

| Page / section | Banner file |
|----------------|------------|
| Home | `banner-8.jpg` |
| Composers section | `banner9.jpg` |
| Blog section | `banner-7.jpg` |
| Translations / Texts | `banneri.jpg` |
| Individual pages (default) | `stabatmater-header-475.jpg` |

A page inherits its parent section's banner if it doesn't define its own. Individual composer pages inherit `banner9.jpg` from `composers/_index.md`.

---

## Images

Images are **not stored in git**. They are downloaded from stabatmater.info at build time (the `curl` step in `.github/workflows/deploy.yml`) and placed in `static/images/`. In templates, reference them as `/stm/images/filename.ext`.

To add a new image, add a `curl` line to the workflow and reference the file in content or templates.

---

## Local development

```bash
hugo server
```

Note: images won't load locally unless you download them manually to `static/images/`.

---

## Deployment

Every `git push` to `main` triggers GitHub Actions:
1. Downloads all images from stabatmater.info into `static/images/`
2. Builds with `hugo --minify`
3. Deploys to GitHub Pages

Build time ~35–45 seconds. GitHub Pages source must be set to **"GitHub Actions"** in Settings → Pages.

---

## Known differences from the original (PoC scope)

- Only 3 composers are present (Pergolesi, Abos, Aichinger) as content examples
- Composer pages use COMPOSERS▾ dropdown in the nav (original uses a hover overlay)
- No search functionality beyond the A–Z filter on the composers list
- No Dutch-language version
