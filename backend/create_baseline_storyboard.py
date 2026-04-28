from pathlib import Path
import json

p = Path('backend/day7_coffee_storyboard.json')
text = json.loads(p.read_text(encoding='utf-8'))
text['project_id'] = 'day7_coffee_baseline_static'
text['title'] = text['title'] + ' (Baseline static)'
Path('backend/day7_coffee_baseline_static_storyboard.json').write_text(json.dumps(text, indent=2), encoding='utf-8')
print('baseline storyboard created')
