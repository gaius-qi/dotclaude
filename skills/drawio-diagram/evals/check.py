"""Grade a run dir against evals.json assertions: reads <run>/outputs/*.drawio + *.png, writes <run>/grading.json. Usage: python3 check.py <run_dir>"""
import glob, json, re, sys, os
run = sys.argv[1]
out = os.path.join(run, 'outputs')
drawio = glob.glob(f'{out}/*.drawio'); png = glob.glob(f'{out}/*.png')
xml = open(drawio[0]).read() if drawio else ''
cells = re.findall(r'<mxCell\b[^>]*>', xml)
styles = [re.search(r'style="([^"]*)"', c).group(1) for c in cells if 'style="' in c]
vert = [re.search(r'style="([^"]*)"', c).group(1) for c in cells if 'vertex="1"' in c and 'style="' in c]
vert = [s for s in vert if not s.startswith('text;') and 'curlyBracket' not in s]
fills = {c.upper() for c in re.findall(r'fillColor=(#[0-9A-Fa-f]{6})', xml)}
allowed = {'#CBDCFD','#E6EDFC','#99B9FB','#D9EACC','#F0FAE9','#C3E4A9','#FFF0CD','#FFF8E6','#FDD09B','#FDD1D1','#FFF0F0','#C1EDFD','#D1F4EE','#F5F5F5','#E8F8E9','#FFFFFF'}
edges = re.findall(r'<mxCell[^>]*edge="1"[^>]*style="([^"]*)"', xml) or [s for s in styles if 'Arrow=' in s or 'edgeStyle' in s]
edge_styles = [m for m in re.findall(r'<mxCell[^>]*?style="([^"]*)"[^>]*?edge="1"', xml)] + [m for m in re.findall(r'<mxCell[^>]*?edge="1"[^>]*?style="([^"]*)"', xml)]
checks = [
 ('drawio 和 png 都产出', bool(drawio and png), f'drawio={drawio} png={png}'),
 ('填充色只用 perf-tools 调色板', bool(fills) and fills <= allowed, f'fills={sorted(fills)}'),
 ('所有描边为黑色', bool(xml) and not re.search(r'strokeColor=#(?!000000)[0-9A-Fa-f]{6}', xml), 'non-black strokeColor found' if re.search(r'strokeColor=#(?!000000)[0-9A-Fa-f]{6}', xml) else 'ok'),
 ('描边 1.5px 或 1px', bool(vert) and all(('strokeWidth=1.5' in s or 'strokeWidth=1' in s or 'strokeColor=none' in s) for s in vert), f'{sum("strokeWidth=2" in s and "rounded=1" in s for s in vert)}/{len(vert)} vertices'),
 ('箭头是开放式 V 形 (endArrow=open, endFill=0)', bool(edge_styles) and all('endArrow=open' in s and 'endFill=0' in s for s in edge_styles if 'endArrow=none' not in s), f'{len(edge_styles)} edges'),
 ('箭头不用 orthogonalEdgeStyle 自动折线', bool(xml) and 'orthogonalEdgeStyle' not in xml, 'ok' if 'orthogonalEdgeStyle' not in xml else 'found orthogonalEdgeStyle'),
 ('填充色不超过 5 种（不含注释框）', bool(xml) and len({c.upper() for c in re.findall(r'fillColor=(#[0-9A-Fa-f]{6})', xml)} - {'#F5F5F5','#E8F8E9','#FFF0F0','#FFFFFF'}) <= 5, f'{len({c.upper() for c in re.findall(r"fillColor=(#[0-9A-Fa-f]{6})", xml)} - {"#F5F5F5","#E8F8E9","#FFF0F0","#FFFFFF"})} fills'),
 ('图内没有中文字符', bool(xml) and not re.search(r'[\u4e00-\u9fff]', xml), 'chinese found' if re.search(r'[\u4e00-\u9fff]', xml) else 'ok'),
 ('无阴影/渐变', bool(xml) and 'shadow=1' not in xml and 'gradientColor' not in xml, 'ok'),
]
exp=[{'text': t, 'passed': bool(p), 'evidence': e} for t, p, e in checks]; n=sum(x['passed'] for x in exp)
json.dump({'expectations': exp, 'summary': {'passed': n, 'failed': len(exp)-n, 'total': len(exp), 'pass_rate': n/len(exp)}}, open(os.path.join(run, 'grading.json'), 'w'), ensure_ascii=False, indent=1)
print(run, sum(p for _, p, _ in checks), '/', len(checks))
