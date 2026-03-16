# stabatmater-hugo

Testomgeving voor de migratie van stabatmater.info van WordPress naar Hugo + GitHub Pages.

⚠️ **Dit is een TEST-site.** De productiewebsite staat op [stabatmater.info](https://stabatmater.info).
De site is voorzien van `robots.txt` en `noindex` meta tags zodat zoekmachines hem niet indexeren.

## Structuur

```
content/
  composers/     ← één .md bestand per componist
  blog/          ← één .md bestand per blogpost
  translations/  ← vertaalpagina's
  texts/         ← uitleg over het gedicht
```

## Componist toevoegen of aanpassen

Elk componistbestand heeft deze structuur:

```yaml
---
title: "Naam van de componist"
born: 1710
died: 1736
country: "Land"
period: "Barok"
duration_minutes: 33
forces: "sopraan, orkest"
cds:
  - title: "CD-titel"
    label: "Label"
    conductor: "Dirigent"
    soloists: "Solisten"
    code: "CODE 01"
---

Tekst over de componist...
```

## Blogpost toevoegen

Maak een nieuw bestand in `content/blog/` met naam `YYYY-MM-DD-titel.md`:

```yaml
---
title: "Titel van de post"
date: 2025-06-01
summary: "Korte samenvatting voor de bloglijst."
---

Inhoud van de blogpost...
```

## Lokaal draaien

```bash
hugo server
```

## Automatisch deployen

Bij elke `git push` naar `main` bouwt GitHub Actions de site automatisch en publiceert hem op GitHub Pages.
