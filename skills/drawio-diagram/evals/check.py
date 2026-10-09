"""Grade a run dir against evals.json assertions: reads <run>/outputs/*.drawio + *.png, writes <run>/grading.json. Usage: python3 check.py <run_dir>
Style checks come from scripts/lint.py so the eval and the pre-delivery lint can never disagree."""
import glob, json, re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from lint import checks
run = sys.argv[1]
out = os.path.join(run, 'outputs')
drawio = glob.glob(f'{out}/*.drawio'); png = glob.glob(f'{out}/*.png')
xml = open(drawio[0]).read() if drawio else ''
L = {name: (ok, ev) for name, ok, ev in checks(xml)} if xml else {}
def lint(name): return (bool(xml) and L[name][0], L[name][1] if xml else 'no drawio')
checks_ = [
 ('drawio 和 png 都产出', bool(drawio and png), f'drawio={drawio} png={png}'),
 ('填充色只用 perf-tools 调色板', *lint('fills from the palette only')),
 ('所有描边为黑色', *lint('all strokes black (faint grey only for ruler ticks)')),
 ('描边 1.5px 或 1px', *lint('vertex strokes 1.5px or 1px')),
 ('箭头是开放式 V 形 (endArrow=open, endFill=0)', *lint('arrowheads open V (endArrow=open, endFill=0)')),
 ('箭头不用 orthogonalEdgeStyle 自动折线', *lint('no orthogonalEdgeStyle auto-routing')),
 ('填充色不超过 5 种（不含注释框）', *lint('box fills ≤ 5 families (-bg, note and -strong fills not counted)')),
 ('图内没有中文字符', bool(xml) and not re.search(r'[\u4e00-\u9fff]', xml), 'chinese found' if re.search(r'[\u4e00-\u9fff]', xml) else 'ok'),
 ('无阴影/渐变', *lint('no shadow / gradient')),
]
exp=[{'text': t, 'passed': bool(p), 'evidence': e} for t, p, e in checks_]; n=sum(x['passed'] for x in exp)
json.dump({'expectations': exp, 'summary': {'passed': n, 'failed': len(exp)-n, 'total': len(exp), 'pass_rate': n/len(exp)}}, open(os.path.join(run, 'grading.json'), 'w'), ensure_ascii=False, indent=1)
print(run, n, '/', len(exp))
