/**
 * extract_composer.js
 *
 * Paste this into the Chrome DevTools console (or run via the Claude in Chrome
 * javascript_tool) while viewing a stabatmater.info composer page.
 *
 * Outputs structured text lines that convert_composer.py can parse deterministically.
 *
 * Format:
 *   TITLE: <name>
 *   COUNTRY_CLASS: <slug>          (from WordPress CSS class geboorteland-xxx)
 *   BIO: <paragraph text>          (one line per <p> tag)
 *   META_Date: <value>
 *   META_Performers: <value>
 *   META_Length: <value>
 *   META_Particulars: <value>
 *   META_Textual variations: <value>
 *   CD_CDN: <title>                (N = 1, 2, 3 ...)
 *   CD_More info: <notes>
 *   CD_Orchestra: <name>
 *   CD_Choir: <name>               (optional)
 *   CD_Conductor: <name>           (optional)
 *   CD_Soloists: <names>           (br-tags become '; ')
 *   CD_Other works: <works>        (optional, br-tags become '; ')
 *   CD_Code: <code>
 *   CD_END
 *   COLORBAR: <filename.gif>       (one per colorbar image)
 *   YOUTUBE: <videoId> | <title>   (one per iframe)
 */
(function() {
  var lines = [];

  // Helper: extract text from a td element, converting <br> to '; '
  function tdText(td) {
    if (!td) return '';
    return td.innerHTML
      .replace(/<br\s*\/?>/gi, '; ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#8211;/g, '–')
      .replace(/&#8212;/g, '—')
      .replace(/&#8216;/g, '\u2018')
      .replace(/&#8217;/g, '\u2019')
      .replace(/&#8220;/g, '\u201C')
      .replace(/&#8221;/g, '\u201D')
      .replace(/\s+/g, ' ')
      .trim();
  }

  // --- TITLE ---
  var h1 = document.querySelector('.entry-content h1');
  lines.push('TITLE: ' + (h1 ? h1.textContent.replace(/\s+/g, ' ').trim() : ''));

  // --- COUNTRY (from WordPress article CSS class geboorteland-xxx) ---
  var article = document.querySelector('article');
  var classes = article ? article.className : '';
  var countryMatch = classes.match(/geboorteland-(\S+)/);
  lines.push('COUNTRY_CLASS: ' + (countryMatch ? countryMatch[1] : ''));

  // --- BIO PARAGRAPHS ---
  var h2s = Array.from(document.querySelectorAll('.entry-content h2'));
  var bioH2 = h2s.find(function(h) { return h.textContent.trim() === 'About the composer'; });
  if (bioH2) {
    var el = bioH2.nextElementSibling;
    while (el && el.tagName !== 'H2') {
      if (el.tagName === 'P') {
        var para = el.textContent.replace(/\s+/g, ' ').trim();
        if (para) lines.push('BIO: ' + para);
      }
      el = el.nextElementSibling;
    }
  }

  // --- METADATA TABLE (first table: Date, Performers, Length, Particulars, Textual variations) ---
  var tables = document.querySelectorAll('.entry-content table');
  if (tables.length > 0) {
    tables[0].querySelectorAll('tr').forEach(function(r) {
      var tds = r.querySelectorAll('td');
      if (tds.length < 2) return;
      var k = tds[0].textContent.replace(/:/g, '').trim();
      if (!k || k === 'Colour bar') return;  // skip colour bar (images only)
      var v = tdText(tds[1]);
      if (v) lines.push('META_' + k + ': ' + v);
    });
  }

  // --- CD TABLES (one table per CD) ---
  for (var ti = 1; ti < tables.length; ti++) {
    tables[ti].querySelectorAll('tr').forEach(function(r) {
      var tds = r.querySelectorAll('td');
      if (tds.length < 2) return;
      var k = tds[0].textContent.replace(/:/g, '').trim();
      var v = tdText(tds[1]);
      if (k && v) lines.push('CD_' + k + ': ' + v);
    });
    lines.push('CD_END');
  }

  // --- COLORBAR IMAGES ---
  Array.from(document.querySelectorAll('.entry-content img')).forEach(function(img) {
    var src = img.getAttribute('src') || '';
    if (src.includes('colorbar')) {
      lines.push('COLORBAR: ' + src.split('/').pop());
    }
  });

  // --- YOUTUBE (video ID only — avoids query-string output filter) ---
  Array.from(document.querySelectorAll('.entry-content iframe')).forEach(function(f) {
    var src = f.getAttribute('src') || '';
    var title = (f.getAttribute('title') || '').replace(/\|/g, '-');
    // Extract video ID from /embed/VIDEO_ID
    var m = src.match(/embed\/([\w-]+)/);
    var vid = m ? m[1] : '';
    if (vid) lines.push('YOUTUBE: ' + vid + ' | ' + title);
    // For playlists (/embed/videoseries) also capture the list ID
    var listM = src.match(/list=([\w-]+)/);
    if (listM && vid === 'videoseries') {
      lines.push('YOUTUBE_LIST: ' + listM[1] + ' | ' + title);
    }
  });

  return lines.join('\n');
})();
