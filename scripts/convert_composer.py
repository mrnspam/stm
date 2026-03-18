#!/usr/bin/env python3
"""
convert_composer.py

Converts a stabatmater.info composer page to a Hugo markdown file.
Content is extracted verbatim from the source; nothing is LLM-generated.

PRIMARY INPUT:  output of Chrome get_page_text MCP tool  (never truncated)
SECONDARY INPUT: YouTube video IDs and colorbar filenames via CLI flags
                 (fetched via short JS calls that are never truncated)

Usage:
    python3 scripts/convert_composer.py <slug> <page_text_file> [options]

Options:
    --youtube "VIDEO_ID | Title"    Add YouTube embed (repeat for multiple)
    --colorbar filename.gif          Add colorbar image (repeat for multiple)
    --country  "Country Name"        Override auto-detected country

Examples:
    # Minimal — text only:
    python3 scripts/convert_composer.py girolamo-abos /tmp/abos.txt

    # With YouTube and colorbar:
    python3 scripts/convert_composer.py girolamo-abos /tmp/abos.txt \\
        --youtube "sbgIqGmMc1A | Stabat Mater - Girolamo Abos" \\
        --colorbar "colorbar-abos.gif"

Output:  content/composers/<slug>.md

---
Workflow for adding a new composer
---
1. In Chrome, navigate to https://stabatmater.info/composers/<SLUG>/
   (the site redirects to /componist/ — that is fine)

2. Run get_page_text MCP tool on the tab. Save the output to /tmp/<slug>.txt

3. Run a SHORT JS call for YouTube IDs (never hits truncation):
       Array.from(document.querySelectorAll('.entry-content iframe'))
           .map(f => {
               var src = f.getAttribute('src') || '';
               var m = src.match(/embed\\/([\w-]+)/);
               return (m ? m[1] : '') + ' | ' + (f.getAttribute('title') || '');
           }).join('\\n')
   Note each "ID | Title" line; add as --youtube flags.

4. Run a SHORT JS call for colorbar filenames:
       Array.from(document.querySelectorAll('.entry-content img'))
           .filter(i => (i.getAttribute('src')||'').includes('colorbar'))
           .map(i => i.getAttribute('src').split('/').pop()).join('\\n')
   Note each filename; add as --colorbar flags.

5. python3 scripts/convert_composer.py <slug> /tmp/<slug>.txt \\
       --youtube "ID | Title" \\
       --colorbar "colorbar-name.gif"

6. Inspect the output, then: git add content/composers/<slug>.md && git commit
"""

import sys
import re
import os
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'content', 'composers'))

# Map WordPress geboorteland-XXX CSS class slug → display name.
# The slug comes from the article HTML class attribute, not needed for get_page_text mode.
# Keep for reference / future structured mode.
COUNTRY_MAP = {
    'austria': 'Austria', 'belgium': 'Belgium', 'bohemia': 'Bohemia',
    'brazil': 'Brazil', 'canada': 'Canada', 'czechia': 'Czech Republic',
    'denmark': 'Denmark', 'england': 'England', 'finland': 'Finland',
    'france': 'France', 'germany': 'Germany', 'hungary': 'Hungary',
    'ireland': 'Ireland', 'italy': 'Italy', 'malta': 'Malta',
    'mexico': 'Mexico', 'netherlands': 'Netherlands', 'norway': 'Norway',
    'poland': 'Poland', 'portugal': 'Portugal', 'russia': 'Russia',
    'scotland': 'Scotland', 'slovakia': 'Slovakia', 'spain': 'Spain',
    'sweden': 'Sweden', 'switzerland': 'Switzerland', 'ukraine': 'Ukraine',
    'usa': 'USA', 'wales': 'Wales',
}

# Known field labels in "About the Stabat Mater" section (ORDER matters for parsing)
META_FIELDS = ['Date', 'Performers', 'Length', 'Particulars', 'Textual variations', 'Colour bar']

# Known field labels within each CD block (ORDER matters for parsing)
CD_FIELDS = ['More info', 'Orchestra', 'Choir', 'Conductor', 'Soloists', 'Other works', 'Code']


# ── Parsing ───────────────────────────────────────────────────────────────────

def strip_header(text):
    """Remove the get_page_text header (Title:, URL:, Source element:, ---)."""
    if text.lstrip().startswith('Title:'):
        m = re.search(r'^---\s*\n', text, re.MULTILINE)
        if m:
            return text[m.end():]
    return text


def extract_section(text, start_marker, end_marker):
    """Return text between start_marker and end_marker (exclusive)."""
    s = text.find(start_marker)
    if s == -1:
        return ''
    s += len(start_marker)
    e = text.find(end_marker, s)
    return (text[s:e] if e != -1 else text[s:]).strip()


def parse_fields(text, field_names):
    """
    Split `text` on known field labels (e.g. "Date:", "Performers:") and return
    a dict mapping each field name to its verbatim value.

    The regex anchors on KNOWN field names only, so colons in values
    (e.g. "CD 1: 30 min", "Tartini: Stabat Mater") are not treated as delimiters.
    """
    pattern = r'(?<!\w)(' + '|'.join(re.escape(f) for f in field_names) + r'):\s*'
    tokens = re.split(pattern, text)
    result = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i].strip()
        if tok in field_names and i + 1 < len(tokens):
            val = tokens[i + 1].strip()
            result[tok] = val
            i += 2
        else:
            i += 1
    return result


def parse_cds(cd_section):
    """
    Split the recording section into individual CD dicts.
    The section looks like:
      CD1: title More info: notes Orchestra: ... Code: X  CD2: title ...
    """
    # Split on CDN: or CD: marker (lookahead keeps the marker in each block)
    blocks = re.split(r'(?=\bCD\d*:\s)', cd_section.strip())
    cds = []
    for block in blocks:
        block = block.strip()
        if not re.match(r'CD\d*:\s', block):
            continue
        # Strip "CDN: " or "CD: " prefix
        m = re.match(r'CD\d*:\s*(.*)', block, re.DOTALL)
        if not m:
            continue
        rest = m.group(1).strip()

        # Separate title (everything before the first known CD field)
        first_field = re.search(
            r'(?<!\w)(?:' + '|'.join(re.escape(f) for f in CD_FIELDS) + r'):\s',
            rest
        )
        if first_field:
            title = rest[:first_field.start()].strip()
            fields_text = rest[first_field.start():]
        else:
            title = rest.strip()
            fields_text = ''

        fields = parse_fields(fields_text, CD_FIELDS)

        cd = {'title': title}
        field_map = {
            'More info':   'notes',
            'Orchestra':   'orchestra',
            'Choir':       'choir',
            'Conductor':   'conductor',
            'Soloists':    'soloists',
            'Other works': 'other_works',
            'Code':        'code',
        }
        for src, dst in field_map.items():
            val = fields.get(src, '').strip()
            if val:
                cd[dst] = val

        cds.append(cd)
    return cds


def extract_years(bio_text):
    """
    Extract born/died years from the bio text.
    Handles patterns:
      - "LASTNAME (1710 – 1736)"
      - "born ... in 1715" / "died in 1760"
    """
    born = died = None
    m = re.search(r'\((\d{4})\s*[–\-]\s*(\d{4})\)', bio_text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r'\bborn\b.{0,80}?\bin (\d{4})', bio_text)
    if m:
        born = int(m.group(1))
    m = re.search(r'\bdied\b.{0,60}?(\d{4})', bio_text)
    if m:
        died = int(m.group(1))
    return born, died


# ── YAML helpers ──────────────────────────────────────────────────────────────

def yq(val):
    """Return value as a double-quoted YAML string."""
    return '"' + str(val).strip().replace('\\', '\\\\').replace('"', '\\"') + '"'


def yblock(val, indent=6):
    """Return value as a YAML block scalar (>-)."""
    ind = ' ' * indent
    return '>-\n' + ind + val.strip().replace('\n', '\n' + ind)


def yval(val, threshold=100, indent=6):
    """Use inline quoting for short values, block scalar for long ones."""
    v = val.strip()
    return yblock(v, indent) if (len(v) > threshold or '\n' in v) else yq(v)


# ── Generation ────────────────────────────────────────────────────────────────

def build_front_matter(slug, title, bio_text, meta, cds, youtube, colorbars, country_override, period_override=''):
    born, died = extract_years(bio_text)
    country = country_override  # passed from CLI (or empty)

    lines = ['---']
    lines.append('title: ' + yq(title))
    if born:
        lines.append('born: ' + str(born))
    if died:
        lines.append('died: ' + str(died))
    if country:
        lines.append('country: ' + yq(country))
    if period_override:
        lines.append('period: ' + yq(period_override))
    lines.append('banner: "banneri.jpg"')

    if youtube:
        lines.append('youtube:')
        for yt in youtube:
            lines.append('  - url: ' + yq(yt['url']))
            lines.append('    title: ' + yq(yt['title']))

    if cds:
        lines.append('cds:')
        for cd in cds:
            lines.append('  - title: ' + yq(cd.get('title', '')))
            for field in ['notes', 'orchestra', 'choir', 'conductor',
                          'soloists', 'other_works', 'code']:
                v = cd.get(field, '').strip()
                if not v:
                    continue
                lines.append('    ' + field + ': ' + yval(v, threshold=100, indent=6))

    lines.append('---')
    return '\n'.join(lines)


def build_body(bio_text, section_data):
    """
    Build body for one or more Stabat Mater sections.
    section_data: list of (meta_dict, colorbar_list) — one entry per SM section.
    """
    lines = []

    lines.append('## About the composer')
    lines.append('')
    lines.append(bio_text.strip())
    lines.append('')

    for meta, colorbars in section_data:
        lines.append('## About the Stabat Mater')
        lines.append('')
        lines.append('<table class="stabat-table">')
        for label in ['Date', 'Performers', 'Length', 'Particulars', 'Textual variations']:
            v = meta.get(label, '').strip()
            if v:
                lines.append('<tr><th>' + label + '</th><td>' + v + '</td></tr>')
        if colorbars:
            imgs = ' '.join(
                '<a href="/stm/images/{f}"><img src="/stm/images/{f}" alt="{f}"></a>'.format(f=f)
                for f in colorbars
            )
            lines.append('<tr><th>Colour bar</th><td>' + imgs + '</td></tr>')
        lines.append('</table>')
        lines.append('')

    return '\n'.join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def convert(slug, raw_text, youtube_args, colorbar_args, country_override, period_override=''):
    text = strip_header(raw_text)
    # Collapse multiple spaces/newlines to single space for flat-text parsing
    flat = re.sub(r'\s+', ' ', text).strip()

    # --- Title ---
    m = re.search(r'^(.+?)\s+About the composer\b', flat, re.IGNORECASE)
    title = re.sub(r'\s+', ' ', m.group(1)).strip() if m else slug.replace('-', ' ').title()

    # --- Bio ---
    bio_text = extract_section(flat, 'About the composer', 'About the Stabat Mater').strip()

    # --- Split into one chunk per Stabat Mater section ---
    # Each chunk is the text after 'About the Stabat Mater' up to the next occurrence
    sm_chunks = flat.split('About the Stabat Mater')[1:]  # skip everything before first

    colorbars = [c.strip() for c in colorbar_args if c.strip()]

    all_cds = []
    section_data = []  # list of (meta_dict, colorbar_list_for_this_section)

    for i, chunk in enumerate(sm_chunks):
        # Meta: everything before 'Colour bar:' or 'Information about the recording'
        if 'Colour bar:' in chunk:
            meta_raw = chunk[:chunk.find('Colour bar:')]
        elif 'Information about the recording' in chunk:
            meta_raw = chunk[:chunk.find('Information about the recording')]
        else:
            meta_raw = chunk
        meta = parse_fields(meta_raw, META_FIELDS)

        # CDs: between 'Information about the recording' and ' Listen'
        cd_text = extract_section(chunk, 'Information about the recording', ' Listen')
        section_cds = parse_cds(cd_text) if cd_text else []
        all_cds.extend(section_cds)

        # Assign colorbars in order: one per section
        cb = [colorbars[i]] if i < len(colorbars) else []
        section_data.append((meta, cb))

    # --- YouTube (from CLI) ---
    youtube = []
    for raw in youtube_args:
        parts = raw.split('|', 1)
        vid = parts[0].strip()
        yt_title = parts[1].strip() if len(parts) > 1 else ''
        # If vid already contains query params (e.g. videoseries?list=XXX), use as-is
        if '?' in vid:
            url = 'https://www.youtube.com/embed/' + vid
        else:
            url = 'https://www.youtube.com/embed/' + vid + '?feature=oembed'
        youtube.append({'url': url, 'title': yt_title})

    front_matter = build_front_matter(
        slug, title, bio_text, {}, all_cds, youtube, [], country_override, period_override
    )
    body = build_body(bio_text, section_data)
    return front_matter + '\n\n' + body


def main():
    parser = argparse.ArgumentParser(
        description='Convert stabatmater.info page text to Hugo markdown.')
    parser.add_argument('slug', help='Composer slug, e.g. girolamo-abos')
    parser.add_argument('page_text_file',
                        help='Path to page text file from Chrome get_page_text')
    parser.add_argument('--youtube', metavar='"ID | Title"', action='append', default=[],
                        help='YouTube video ID and title (repeat for multiple)')
    parser.add_argument('--colorbar', metavar='filename.gif', action='append', default=[],
                        help='Colorbar image filename (repeat for multiple)')
    parser.add_argument('--country', metavar='"Country Name"', default='',
                        help='Country name (if auto-detection is insufficient)')
    parser.add_argument('--period', metavar='"Baroque"', default='',
                        help='Period (Medieval/Renaissance/Baroque/Classical/Romantic/Modern/Contemporary)')
    args = parser.parse_args()

    with open(args.page_text_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    result = convert(args.slug, raw_text, args.youtube, args.colorbar, args.country, args.period)

    os.makedirs(CONTENT_DIR, exist_ok=True)
    output_file = os.path.join(CONTENT_DIR, args.slug + '.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)

    # Summary
    flat = re.sub(r'\s+', ' ', strip_header(raw_text))
    sm_count = flat.count('About the Stabat Mater')
    cd_count = len(re.findall(r'\bCD\d*:\s', flat))
    print('Written : ' + output_file)
    print('YouTube : ' + str(len(args.youtube)) + ' entries')
    print('SM sects: ' + str(sm_count) + ' detected')
    print('CDs     : ' + str(cd_count) + ' detected')


if __name__ == '__main__':
    main()
