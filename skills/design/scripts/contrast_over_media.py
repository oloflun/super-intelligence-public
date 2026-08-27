"""Contrast for text over media, measured from rendered pixels.

Computed style cannot answer this: the ground is a video frame. So the text is
hidden, the hero is screenshotted, and the luminance of the exact rectangle each
string occupied is sampled from that plate. Worst case uses the brightest patch
under the string, not the mean, because one blown highlight is where the text
actually disappears.
"""
import io
from PIL import Image
from playwright.sync_api import sync_playwright

TARGETS = "h1, header nav a, header a, section p, section a[href='#meny']"


def lum_srgb(px):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = px[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    pg.goto('http://localhost:3055/', wait_until='networkidle')
    pg.wait_for_timeout(2500)

    boxes = pg.evaluate("""(sel) => {
      const out = [];
      document.querySelectorAll(sel).forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width < 4 || r.height < 4 || r.top > innerHeight || r.bottom < 0) return;
        const t = el.innerText.trim();
        if (!t) return;
        out.push({t: t.slice(0,24).replace(/\\s+/g,' '),
                  x: Math.max(0, r.left), y: Math.max(0, r.top),
                  w: r.width, h: r.height,
                  color: getComputedStyle(el).color,
                  size: parseFloat(getComputedStyle(el).fontSize)});
      });
      return out;
    }""", TARGETS)

    # hide every text node in the fold, then plate the background alone
    pg.add_style_tag(content="h1,h2,p,a,span,nav,button{color:transparent!important;"
                             "text-shadow:none!important;border-color:transparent!important}"
                             "svg,img.logo{opacity:0!important}")
    pg.wait_for_timeout(500)
    plate = Image.open(io.BytesIO(pg.screenshot())).convert('RGB')
    b.close()

print(f"{len(boxes)} strangar over media, matta mot plattan:\n")
for bx in boxes:
    x0, y0 = int(bx['x']), int(bx['y'])
    x1, y1 = int(bx['x'] + bx['w']), int(bx['y'] + bx['h'])
    crop = plate.crop((x0, y0, min(x1, plate.width), min(y1, plate.height)))
    px = list(crop.getdata())
    if not px:
        continue
    lums = sorted(lum_srgb(q) for q in px)
    worst = lums[int(len(lums) * 0.95)]          # brightest 5% of the ground
    mean = sum(lums) / len(lums)
    fg = 1.0 if '255, 255, 255' in bx['color'] else 0.0   # white text
    ratio_worst = (max(fg, worst) + 0.05) / (min(fg, worst) + 0.05)
    ratio_mean = (max(fg, mean) + 0.05) / (min(fg, mean) + 0.05)
    floor = 3 if bx['size'] >= 24 else 4.5
    mark = 'ok  ' if ratio_worst >= floor else 'FAIL'
    print(f"{mark} varsta {ratio_worst:5.2f}:1  medel {ratio_mean:5.2f}:1  "
          f"(golv {floor})  {int(bx['size'])}px  {bx['t']!r}")
