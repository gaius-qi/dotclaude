"""Minimal draw.io XML builder in the house style.
from dio import Diagram; d = Diagram(); a = d.box('T', 0,0,200,60,'primary', sub='desc'); d.edge(a, b, label='x'); d.save('x.drawio'); Diagram.export('x.drawio','x.png')
"""
import html, os, shutil, subprocess

INK = '#000000'                                              # text, strokes, arrows (Gregg: black on pastel)
# Palette lifted from Brendan Gregg's Linux perf tools diagram. Colour = subsystem family, not decoration.
FILL = {
    'blue': '#CBDCFD', 'blue-bg': '#E6EDFC', 'blue-strong': '#99B9FB',      # storage / filesystem / data path
    'green': '#D9EACC', 'green-bg': '#F0FAE9', 'green-strong': '#C3E4A9',   # network / transport / P2P
    'yellow': '#FFF0CD', 'yellow-bg': '#FFF8E6', 'orange': '#FDD09B',       # compute / scheduling / memory / hardware
    'red': '#FDD1D1', 'red-bg': '#FFF0F0',                                  # application / user-facing / registry
    'cyan': '#C1EDFD', 'mint': '#D1F4EE',                                   # drivers / firmware / base layers
    'grey': '#F5F5F5',                                                      # neutral: start/end, misc
}
NOTE_FILL = {'grey': '#F5F5F5', 'green': '#E8F8E9', 'pink': '#FFF0F0'}     # observability / static-config / tracing
LIGHT = '#FFFFFF'
MONO = 'Courier New, Menlo, monospace'
SANS = 'Trebuchet MS, Helvetica Neue, PingFang SC, sans-serif'
STROKE = f'strokeColor={INK};strokeWidth=1.5;'
FAMILY = f'fontFamily={SANS};'
FONT = f'fontColor={INK};fontSize=14;' + FAMILY
BOX = 'rounded=1;absoluteArcSize=1;arcSize=12;whiteSpace=wrap;html=1;' + STROKE + FONT
PILL = 'rounded=1;arcSize=50;whiteSpace=wrap;html=1;' + STROKE + FONT
RHOMBUS = 'rhombus;whiteSpace=wrap;html=1;' + STROKE + FONT
TEXT = 'text;html=1;align=center;verticalAlign=middle;strokeColor=none;fillColor=none;' + FONT
FRAME = f'rounded=1;absoluteArcSize=1;arcSize=12;html=1;fillColor=none;dashed=1;dashPattern=4 4;fixDash=1;strokeColor={INK};strokeWidth=1;' + FONT
GROUP = f'rounded=1;absoluteArcSize=1;arcSize=12;html=1;strokeColor=none;fontColor={INK};fontSize=13;' + FAMILY
TITLE = 'align=left;verticalAlign=top;spacingLeft=10;spacingTop=4;fontStyle=1;'
NOTE = f'rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=1 3;fixDash=1;strokeColor={INK};strokeWidth=1;fontColor={INK};fontSize=12;fontStyle=1;fontFamily={MONO};'
EDGE = f'html=1;endArrow=open;endFill=0;endSize=8;labelBackgroundColor=none;strokeColor={INK};strokeWidth=1.5;fontColor={INK};fontSize=13;' + FAMILY
DOTTED = f'html=1;endArrow=none;dashed=1;dashPattern=1 3;fixDash=1;strokeColor={INK};strokeWidth=1;'
BRACE = 'shape=curlyBracket;rounded=1;html=1;fillColor=none;' + STROKE

def esc(s): return html.escape(str(s), quote=True).replace('\n', '&lt;br&gt;')

class Diagram:
    def __init__(self): self.cells, self.n = [], 0
    def _id(self): self.n += 1; return f'c{self.n}'
    def _v(self, label, style, x, y, w, h, id=None):
        id = id or self._id()
        self.cells.append(f'<mxCell id="{id}" value="{esc(label)}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" as="geometry"/></mxCell>')
        return id
    @staticmethod
    def _label(title, sub, bold):
        """Component name bold (it is the thing the reader scans for); subtitle smaller italic."""
        t = f'<b>{title}</b>' if bold else title
        return f'{t}<br><i><font style="font-size:12px">{sub}</font></i>' if sub else t
    def _fillstyle(self, fill):
        return f'fillColor={FILL.get(fill, fill)};'
    def box(self, title, x, y, w, h, fill='blue', sub='', bold=True, id=None, style=''):
        return self._v(self._label(title, sub, bold), BOX + self._fillstyle(fill) + style, x, y, w, h, id)
    def pill(self, label, x, y, w, h, fill='grey', id=None):
        return self._v(label, PILL + self._fillstyle(fill), x, y, w, h, id)
    def rhombus(self, label, x, y, w, h, fill='yellow', id=None):
        return self._v(f'<b>{label}</b>', RHOMBUS + self._fillstyle(fill), x, y, w, h, id)
    def frame(self, x, y, w, h, label='', id=None, solid=False):
        """Dashed boundary (default) or solid box outline. No fill."""
        st = (BOX + 'fillColor=none;' if solid else FRAME) + (TITLE if label else '')
        return self._v(label, st, x, y, w, h, id)
    def group(self, x, y, w, h, label='', fill='blue-bg', id=None):
        """Filled, borderless background block (layer / subsystem), Gregg-style. Put same-family boxes inside."""
        return self._v(label, GROUP + f'fillColor={FILL.get(fill, fill)};' + (TITLE if label else ''), x, y, w, h, id)
    def note(self, text, x, y, w, h, kind='grey', id=None):
        """Dotted annotation box, monospace bold: commands, tool names, config keys.
        kind: 'grey' observability/commands, 'green' static config/files, 'pink' tracing/debug."""
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')   # commands often contain <arg>; keep them literal under html=1
        return self._v(text, NOTE + f'fillColor={NOTE_FILL[kind]};', x, y, w, h, id)
    def text(self, label, x, y, w, h, bold=False, size=14, align='center', id=None):
        return self._v(label, TEXT + ('fontStyle=1;' if bold else '') + f'fontSize={size};align={align};', x, y, w, h, id)
    def brace(self, x1, x2, yc, up=True):
        """Horizontal curly brace spanning [x1,x2], centered on yc. up=True: tip points up."""
        L = x2 - x1
        return self._v('', BRACE + f'rotation={90 if up else -90};', (x1 + x2) / 2 - 10, yc - L / 2, 20, L)
    def _edge_style(self, both, dashed, arrow, bold, lstyle):
        st = EDGE
        if not arrow: st = st.replace('endArrow=open;', 'endArrow=none;')
        if both: st += 'startArrow=open;startFill=0;startSize=8;'
        if dashed: st += 'dashed=1;dashPattern=4 4;fixDash=1;'
        if bold: st += 'fontStyle=1;'
        return st + lstyle
    def _geo(self, pos, offset, points, src_pt=None, dst_pt=None):
        inner = f'<mxPoint x="{offset[0]}" y="{offset[1]}" as="offset"/>' if offset != (0, 0) else ''
        if src_pt: inner += f'<mxPoint x="{src_pt[0]:g}" y="{src_pt[1]:g}" as="sourcePoint"/><mxPoint x="{dst_pt[0]:g}" y="{dst_pt[1]:g}" as="targetPoint"/>'
        if points: inner += '<Array as="points">' + ''.join(f'<mxPoint x="{px:g}" y="{py:g}"/>' for px, py in points) + '</Array>'
        return f'<mxGeometry x="{pos}" relative="1" as="geometry">{inner}</mxGeometry>'
    def edge(self, src, dst, exit=(0.5, 1), entry=(0.5, 0), label='', both=False, dashed=False, arrow=True,
             bold=False, pos=0, offset=(0, 0), points=None, lstyle='', id=None):
        """Edge between cells. exit/entry = (x,y) fractions on the box; align them so the line is straight.
        Label: pos in [-1,1] slides it along the edge (0 = midpoint), offset = pixel shift. Keep labels in the
        gap between shapes, never on a border."""
        st = self._edge_style(both, dashed, arrow, bold, lstyle) + f'exitX={exit[0]};exitY={exit[1]};entryX={entry[0]};entryY={entry[1]};'
        self.cells.append(f'<mxCell id="{id or self._id()}" value="{esc(label)}" style="{st}" edge="1" parent="1" source="{src}" target="{dst}">{self._geo(pos, offset, points)}</mxCell>')
    def hedge(self, src, dst, label='', **kw):
        """Left-to-right edge with the label floating 6px above the line."""
        self.edge(src, dst, (1, .5), (0, .5), label, offset=(0, -6), lstyle='verticalAlign=bottom;', **kw)
    def dotted(self, src, dst, exit=(0.5, 0.5), entry=(0.5, 0.5), points=None, id=None):
        """Dotted leader from a note to the thing it annotates. No arrowhead."""
        st = DOTTED + f'exitX={exit[0]};exitY={exit[1]};entryX={entry[0]};entryY={entry[1]};'
        self.cells.append(f'<mxCell id="{id or self._id()}" style="{st}" edge="1" parent="1" source="{src}" target="{dst}">{self._geo(0, (0, 0), points)}</mxCell>')
    def line(self, x1, y1, x2, y2, label='', both=False, dashed=False, arrow=True, bold=False, pos=0, offset=(0, -4),
             points=None, lstyle='verticalAlign=bottom;', id=None):
        """Free edge with absolute endpoints (sequence-diagram messages, lifelines)."""
        st = self._edge_style(both, dashed, arrow, bold, lstyle)
        self.cells.append(f'<mxCell id="{id or self._id()}" value="{esc(label)}" style="{st}" edge="1" parent="1">{self._geo(pos, offset, points, (x1, y1), (x2, y2))}</mxCell>')
    def selfcall(self, cx, y, label='', w=60, h=40):
        """Sequence-diagram self message: a square loop on lifeline cx from y to y+h, label to its right."""
        self.line(cx, y, cx, y + h, points=[(cx + w, y), (cx + w, y + h)], lstyle='rounded=0;')
        if label: self.text(label, cx + w + 10, y, 260, h, size=13, align='left')
    def save(self, path):
        body = '\n        '.join(self.cells)
        open(path, 'w').write(f'''<mxfile>
  <diagram name="Page-1" id="p1">
    <mxGraphModel grid="1" gridSize="10" page="1" pageWidth="1200" pageHeight="800" background="#FFFFFF">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        {body}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
''')
        return path
    @staticmethod
    def export(drawio, png):
        exe = shutil.which('drawio') or '/Applications/draw.io.app/Contents/MacOS/draw.io'
        if not os.path.exists(exe): return None
        subprocess.run([exe, '-x', '-f', 'png', '-s', '2', '-b', '20', '-o', png, drawio], check=True, capture_output=True)
        return png

if __name__ == '__main__':  # self-check
    d = Diagram(); a = d.box('A', 0, 0, 100, 50, 'orange', sub='desc'); b = d.box('B', 0, 100, 100, 50); d.edge(a, b, label='x'); d.brace(0, 100, 80)
    n = d.note('perf top <pid>', 200, 0, 80, 30, 'pink'); d.dotted(n, a); d.group(-20, -20, 300, 200, 'G', 'yellow-bg')
    d.line(200, 0, 200, 100, dashed=True, arrow=False); d.frame(-20, -20, 300, 200, 'F'); d.selfcall(200, 20, 'check')
    xml = open(d.save('/tmp/dio_check.drawio')).read()
    assert '<root>' in xml and 'endArrow=open' in xml and 'rotation=90' in xml and xml.count('edge="1"') == 4
    assert '&amp;lt;pid&amp;gt;' in xml and '&lt;b&gt;A&lt;/b&gt;' in xml and '&lt;i&gt;' in xml and '#FFF0F0' in xml and '#FFF8E6' in xml and 'dashPattern=1 3' in xml
    print('ok')
