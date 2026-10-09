"""Style lint for .drawio files built with dio.py. Usage: python3 lint.py a.drawio [b.drawio …]  → one line per check, exit 1 on any FAIL.
Run it before Reading the PNG: it catches what the eye skips (a stray colour, a 2px stroke, a filled arrowhead)."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dio import FILL, NOTE_FILL, BG_FILLS, FAINT

ALLOWED = {v.upper() for v in FILL.values()} | {v.upper() for v in NOTE_FILL.values()} | {'#FFFFFF'}

def checks(xml):
    cells = re.findall(r'<mxCell\b[^>]*>', xml)
    vert = [re.search(r'style="([^"]*)"', c).group(1) for c in cells if 'vertex="1"' in c and 'style="' in c]
    vert = [s for s in vert if not s.startswith('text;') and 'curlyBracket' not in s]
    edges = [re.search(r'style="([^"]*)"', c).group(1) for c in cells if 'edge="1"' in c and 'style="' in c]
    fills = {c.upper() for c in re.findall(r'fillColor=(#[0-9A-Fa-f]{6})', xml)}
    strong = {FILL[k].upper() for k in FILL if k.endswith('-strong') or k == 'orange'}
    boxfills = fills - {b.upper() for b in BG_FILLS} - strong          # -strong / orange are shades of a family, budgeted separately
    bad_stroke = re.search(rf'strokeColor=#(?!000000|{FAINT[1:]})[0-9A-Fa-f]{{6}}', xml)
    fams = {f for f in re.findall(r'fontFamily=([^;]*)', xml) if 'mono' not in f}
    return [
        ('fills from the palette only', fills <= ALLOWED, f'fills={sorted(fills - ALLOWED) or "ok"}'),
        ('box fills ≤ 5 families (-bg, note and -strong fills not counted)', len(boxfills) <= 5, f'{len(boxfills)} box fills'),
        ('≤ 2 accent fills (-strong / orange)', len(fills & strong) <= 2, f'{len(fills & strong)} accents'),
        ('all strokes black (faint grey only for ruler ticks)', not bad_stroke, bad_stroke.group(0) if bad_stroke else 'ok'),
        ('vertex strokes 1.5px or 1px', all(('strokeWidth=1.5' in s or 'strokeWidth=1;' in s or 'strokeColor=none' in s) for s in vert), f'{len(vert)} vertices'),
        ('arrowheads open V (endArrow=open, endFill=0)', all('endArrow=open' in s and 'endFill=0' in s for s in edges if 'endArrow=none' not in s), f'{len(edges)} edges'),
        ('no orthogonalEdgeStyle auto-routing', 'orthogonalEdgeStyle' not in xml, 'ok'),
        ('no shadow / gradient', 'shadow=1' not in xml and 'gradientColor' not in xml, 'ok'),
        ('one sans font family', len(fams) <= 1, f'{sorted(fams)}'),
    ]

if __name__ == '__main__':
    rc = 0
    for path in sys.argv[1:]:
        print(path)
        for name, ok, ev in checks(open(path).read()):
            print(f'  {"PASS" if ok else "FAIL"}  {name}  · {ev}'); rc |= not ok
    sys.exit(rc)
