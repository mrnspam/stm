# stabatmater-hugo

Proof-of-concept migration of [stabatmater.info](https://stabatmater.info) from WordPress to Hugo + GitHub Pages.

⚠️ **This is a TEST site.** The production website is at [stabatmater.info](https://stabatmater.info).
The site includes `robots.txt` and `noindex` meta tags so search engines do not index it.

**Live test site:** https://mrnspam.github.io/stm/

---

## Content structure

```
content/
  composers/     ← one .md file per composer
  blog/          ← one .md file per blog post
  translations/  ← translation pages
```

### Adding or editing a composer

File: `content/composers/firstname-lastname.md`

```yaml
---
title: "Composer Name"
born: 1710
died: 1736
country: "Italy"
period: "Baroque"        # Renaissance / Baroque / Classical / Romantic / Modern
duration_minutes: 41
forces: "soprano, alto, strings, organ"
cds:
  - title: "CD title"
    label: "Label and catalogue number"
    conductor: "Name"
    orchestra: "Ensemble"
    soloists: "Name, voice type"
    recorded: "Location, year"
    notes: "Extra info shown on the composer page"
    code: "CODE 01"
---

## About the composer

Free text (English)...

## About the Stabat Mater

**Date:** ...  **Performers:** ...  **Length:** ...
```

### Adding a blog post

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

## Images

Images are not stored in git. They are downloaded from stabatmater.info during the GitHub Actions build (`curl` step in `deploy.yml`) and baked into the deployment. Use `{{ "images/filename" | absURL }}` in templates.

---

## Local development

```bash
hugo server
```

---

## Deployment

Every `git push` to `main` triggers GitHub Actions: downloads images, builds with `hugo --minify`, deploys to GitHub Pages. Build time ~28s.

GitHub Pages source must be set to **"GitHub Actions"** in Settings → Pages.
