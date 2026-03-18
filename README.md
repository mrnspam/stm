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
    _index.md            ← translations index with links to all languages
    latin.md             ← original Latin text (Analecta vs Vatican, 20 stanzas)
    dutch.md             ← 8 Dutch translations (Van der Velden, Wilmink, etc.)
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

## Adding a composer — systematic conversion

Content is converted **deterministically from the original source** using two scripts in `scripts/`. Nothing is LLM-generated.

### Workflow

```bash
# 1. In Chrome, navigate to the composer page on stabatmater.info
#    (URL redirects to /componist/ — that is fine)

# 2. Run the Chrome get_page_text MCP tool on the tab.
#    Save the output verbatim to /tmp/<slug>.txt

# 3. Short JS call in Chrome for YouTube video IDs:
Array.from(document.querySelectorAll('.entry-content iframe'))
  .map(f => {
    var m = (f.getAttribute('src')||'').match(/embed\/([\w-]+)/);
    return (m ? m[1] : '') + ' | ' + (f.getAttribute('title')||'');
  }).join('\n')
#    Note each "VIDEO_ID | Title" line.

# 4. Short JS call for colorbar image filenames:
Array.from(document.querySelectorAll('.entry-content img'))
  .filter(i => (i.getAttribute('src')||'').includes('colorbar'))
  .map(i => i.getAttribute('src').split('/').pop()).join('\n')
#    Note each filename.

# 5. Run the converter:
python3 scripts/convert_composer.py <slug> /tmp/<slug>.txt \
    --youtube "VIDEO_ID | Title" \
    --colorbar "colorbar-name.gif" \
    --country "Italy" \
    --period "Baroque"
#    Output: content/composers/<slug>.md
#
#    --youtube may be repeated for multiple videos.
#    For YouTube playlists, use the full videoseries string:
#      --youtube "videoseries?list=XXXX | Playlist title"
#    --period values (fixed order for chronological view):
#      Medieval / Renaissance / Baroque / Classical / Romantic / Modern / Contemporary

# 6. Add colorbar curl lines to .github/workflows/deploy.yml:
#    For each --colorbar filename.gif, add:
#      curl -sL -o static/images/<filename>.gif \
#        "https://stabatmater.info/wp-content/uploads/colorbar/<filename>.gif"
#    (Check the actual URL via the JS call in step 4 — some colorbars use
#     a different path, e.g. wp-content/uploads/YYYY/MM/filename.gif)

# 7. Review, then commit both files:
git add content/composers/<slug>.md .github/workflows/deploy.yml && git commit -m "Add composer: <name>"
```

### What the scripts do

| Script | Role |
|--------|------|
| `scripts/extract_composer.js` | JS snippet for Chrome DevTools — extracts structured key/value data from the page (alternative to step 2–4 above, useful for shorter pages) |
| `scripts/convert_composer.py` | Python parser — takes `get_page_text` output + CLI flags and writes Hugo front matter + markdown body, all verbatim from the source |

### Composer front matter reference

```yaml
---
title: "Firstname Lastname"
born: 1710          # auto-detected from bio text
died: 1736          # auto-detected from bio text
country: "Italy"    # from --country flag or auto-detected
period: "Baroque"   # from --period flag; used for chronological sort
banner: "banneri.jpg"   # manuscript banner used for all composer pages
youtube:
  - url: "https://www.youtube.com/embed/VIDEO_ID?feature=oembed"
    title: "Stabat Mater - Name"
cds:
  - title: "Label CATNO: Album title"
    notes: "Free-text notes verbatim from original."
    orchestra: "Orchestra name"
    choir: "Choir name"           # optional
    conductor: "Conductor name"   # optional
    soloists: "Name, voice; Name, voice"
    other_works: "Composer: Work; Composer: Work"  # optional
    code: "YYYY ABC 01"
---
```

Body uses `## About the composer` and `## About the Stabat Mater` headings. The Stabat Mater section contains a `<table class="stabat-table">` with Date, Performers, Length, Particulars, Colour bar, and Textual variations rows.

> **Note:** `is_index: true` is reserved for the four sorting index pages. Do not add it to real composer pages.

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

## Current content (PoC)

### Composers (13)

| Slug | Name | Period | Country |
|------|------|--------|---------|
| `giovanni-battista-pergolesi` | Giovanni Battista Pergolesi | Baroque | Italy |
| `girolamo-abos` | Girolamo Abos | Baroque | Malta |
| `gregor-aichinger` | Gregor Aichinger | Renaissance | Germany |
| `antonio-vivaldi` | Antonio Vivaldi | Baroque | Italy |
| `joseph-haydn` | Joseph Haydn | Classical | Austria |
| `rossini` | Gioachino Rossini | Romantic | Italy |
| `verdi` | Giuseppe Verdi | Romantic | Italy |
| `schubert` | Franz Schubert | Romantic | Austria |
| `antonin-dvorak` | Antonín Dvořák | Romantic | Czech Republic |
| `palestrina` | Giovanni Pierluigi da Palestrina | Renaissance | Italy |
| `poulenc` | Francis Poulenc | Modern | France |
| `luigi-boccherini` | Luigi Boccherini | Classical | Italy |
| `scarlatti` | Alessandro Scarlatti | Baroque | Italy |
| `penderecki` | Krzysztof Penderecki | Contemporary | Poland |

### Translations

| File | Content |
|------|---------|
| `latin.md` | Original Latin text — Analecta vs Vatican side-by-side (20 stanzas) |
| `dutch.md` | 8 Dutch translations (Van der Velden, Wilmink, Nolthenius, Vondel, Gezelle, Vissers, Schulte Nordholt, Bennink Janssonius/Hamers) |

---

## Known differences from the original (PoC scope)

- Composer pages use COMPOSERS▾ dropdown in the nav (original uses a hover overlay)
- No search functionality beyond the A–Z filter on the composers list
- No Dutch-language UI (content translations are present, but the site UI is English-only)
