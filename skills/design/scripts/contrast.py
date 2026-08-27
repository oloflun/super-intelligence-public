"""Contrast, measured against the real background each string sits on.

Two traps this avoids:
  * Tailwind 4 emits oklch(); a regex that only understands rgb() silently
    reads "oklch(0.208 0.042 265)" as rgb(0,208,0) and reports nonsense. Every
    colour is normalised through a canvas first.
  * Text over a photo or video has no token background at all. Those are split
    out and must be judged on pixels, not on computed style.
"""
from playwright.sync_api import sync_playwright

JS = """() => {
  // Draw the colour and read the pixel back. Setting fillStyle alone is not
  // enough: Chromium hands oklch() straight back as the same string, so any
  // hex/rgb parser downstream produces NaN. Rasterising forces the conversion
  // and works for every colour space the page can name.
  const el0 = document.createElement('canvas');
  el0.width = el0.height = 1;
  const cv = el0.getContext('2d', { willReadFrequently: true });
  const rgbOf = (c) => {
    cv.clearRect(0, 0, 1, 1);
    cv.fillStyle = c;
    cv.fillRect(0, 0, 1, 1);
    const d = cv.getImageData(0, 0, 1, 1).data;
    return [d[0], d[1], d[2]];
  };
  const norm = (c) => { const [r, g, b] = rgbOf(c); return `rgb(${r},${g},${b})`; };
  const lum = (c) => {
    const [r, g, b] = rgbOf(c).map(v => v / 255)
      .map(v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const ratio = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
  };
  const opaque = (bg) => bg && bg !== 'transparent' && !/rgba\\(0, 0, 0, 0\\)/.test(bg);
  // Walk up for a background. Returns null when a photo/video ancestor is hit
  // first: that string is over media and computed style cannot answer it.
  const groundOf = (el) => {
    let n = el;
    while (n && n !== document.documentElement) {
      const cs = getComputedStyle(n);
      if (n.querySelector && n.querySelector(':scope > video, :scope > img')) {
        const r = n.getBoundingClientRect(), e = el.getBoundingClientRect();
        if (e.top >= r.top - 1 && e.bottom <= r.bottom + 1) return null;
      }
      if (opaque(cs.backgroundColor)) return cs.backgroundColor;
      n = n.parentElement;
    }
    return 'rgb(255,255,255)';
  };
  const rows = [], overMedia = [], seen = new Set();
  document.querySelectorAll('body *').forEach(el => {
    if (el.closest('script, style')) return;
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!hasText) return;
    const cs = getComputedStyle(el);
    const size = parseFloat(cs.fontSize), weight = parseInt(cs.fontWeight) || 400;
    const ground = groundOf(el);
    const sample = el.innerText.trim().slice(0, 24).replace(/\\s+/g, ' ');
    if (ground === null) { if (!seen.has('m' + sample)) { seen.add('m' + sample); overMedia.push({ sample, size: Math.round(size) }); } return; }
    const key = cs.color + '|' + ground + '|' + Math.round(size);
    if (seen.has(key)) return;
    seen.add(key);
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const r = ratio(cs.color, ground);
    rows.push({ sample, size: Math.round(size), color: norm(cs.color), ground: norm(ground),
                ratio: Math.round(r * 100) / 100, floor: large ? 3 : 4.5, pass: r >= (large ? 3 : 4.5) });
  });
  return { rows, overMedia };
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    pg.goto('http://localhost:3055/', wait_until='networkidle')
    pg.wait_for_timeout(1500)
    res = pg.evaluate(JS)
    for r in sorted(res['rows'], key=lambda x: x['ratio']):
        mark = 'FAIL' if not r['pass'] else 'ok  '
        print(f"{mark} {r['ratio']:>6}:1 (golv {r['floor']}) {r['size']:>3}px {r['color']} pa {r['ground']}  {r['sample']!r}")
    fails = [r for r in res['rows'] if not r['pass']]
    print(f"\n{len(res['rows'])} tokenbakgrunder, {len(fails)} under golvet")
    print(f"{len(res['overMedia'])} strangar ligger over foto/video och maste bedomas pa pixlar:")
    for m in res['overMedia']:
        print(f"    {m['size']:>3}px {m['sample']!r}")
    b.close()
