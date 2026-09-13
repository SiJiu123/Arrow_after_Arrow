"""Extract only timestamps/labels from this task's local JSONL; never publish raw chat."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('session', type=Path)
args = parser.parse_args()
rows = [json.loads(line) for line in args.session.read_text(encoding='utf-8').splitlines()]
zone = timezone(timedelta(hours=8))

def at(line):
    return datetime.fromisoformat(rows[line - 1]['timestamp'].replace('Z', '+00:00')).astimezone(zone)

# Source line numbers identify immutable events in this particular task, not reusable templates.
turns = [(2,17,'初次需求说明'), (19,27,'方案讨论'), (29,37,'风格确认'),
         (41,622,'首次开发'), (624,713,'连续点击修复'), (715,810,'返回首页修复'),
         (812,1109,'GitHub上传'), (1114,1143,'优化评估'),
         (1145,1300,'优化实施'), (1312,1336,'博客信息及心得PSP初稿')]
phases = [
    (2,17,'需求分析与游戏设计'), (19,27,'需求分析与游戏设计'), (29,37,'需求分析与游戏设计'),
    (41,131,'开发环境准备与排障'),
    (131,150,'路径逻辑、关卡与首轮测试代码'),
    (150,165,'游戏界面实现'),
    (165,255,'开发环境准备与排障'),
    (255,362,'测试与修改'),
    (362,451,'README与博客及过程材料'),
    (451,622,'Git提交、上传与核验'),
    (624,675,'测试与修改'), (675,682,'README与博客及过程材料'), (682,713,'Git提交、上传与核验'),
    (715,759,'测试与修改'), (759,782,'README与博客及过程材料'), (782,810,'Git提交、上传与核验'),
    (812,1109,'Git提交、上传与核验'),
    (1114,1143,'测试与修改'),
    (1145,1183,'路径逻辑、关卡与首轮测试代码'),
    (1183,1207,'测试与修改'),
    (1207,1289,'README与博客及过程材料'),
    (1289,1300,'Git提交、上传与核验'),
    (1312,1336,'README与博客及过程材料'),
]
for start, end, _ in turns:
    assert rows[start-1]['payload']['type'] == 'task_started'
    assert rows[end-1]['payload']['type'] == 'task_complete'
    contained = [(s,e) for s,e,_ in phases if start <= s and e <= end]
    assert contained[0][0] == start and contained[-1][1] == end
    assert all(a[1] == b[0] for a,b in zip(contained, contained[1:]))

def record(start, end, label):
    return dict(label=label, source_lines=[start,end], start=at(start).isoformat(),
                end=at(end).isoformat(), seconds=round((at(end)-at(start)).total_seconds(),3))

turn_data = [record(*x) for x in turns]
phase_data = [record(*x) for x in phases]
totals = defaultdict(float)
for item in phase_data:
    totals[item['label']] += item['seconds']
total = round(sum(t['seconds'] for t in turn_data),3)
assert abs(sum(totals.values())-total) < .01
result = {'scope':'Completed agent turns through 2026-09-13 22:20:52, excluding idle gaps, personal offline work, and current reconstruction',
          'method':'Turn durations measured from original task events; within-turn module boundaries are retrospective attribution, not stopwatch measurements',
          'turns':turn_data, 'phases':phase_data,
          'module_seconds':dict(totals), 'total_seconds':total}
dest = Path(__file__).resolve().parents[1] / 'docs' / 'evidence' / 'psp_reconstruction.json'
dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
for name, seconds in totals.items():
    print(f'{name}: {seconds:.3f}s / {seconds/60:.2f}min / {seconds/3600:.4f}h')
print(f'TOTAL: {total:.3f}s / {total/60:.2f}min / {total/3600:.4f}h')
for t in turn_data:
    print(t['label'], t['start'][11:19], t['end'][11:19], round(t['seconds']/60,2))
