"""Save reproducible test results and level metrics; no claim of human playtesting."""
from pathlib import Path
import datetime
import io
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from game_core import first_blocker, solve_level
from levels import LEVELS


def main():
    started = datetime.datetime.now().astimezone()
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    metrics = []
    for level in LEVELS:
        remaining = list(level.arrows)
        layers = []
        while remaining:
            free = [a for a in remaining if first_blocker(a, remaining) is None]
            if not free:
                raise ValueError('Unsolvable level')
            layers.append(len(free))
            remaining = [a for a in remaining if a not in free]
        solution = solve_level(level)
        arrows = {a.id: a for a in level.arrows}
        metrics.append({'level': level.name, 'arrows': len(level.arrows),
                        'removal_layers': layers,
                        'solution_row_col_1_based': [[arrows[key].row + 1, arrows[key].col + 1]
                                                     for key in solution]})
    evidence = ROOT / 'docs' / 'evidence'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'tests.txt').write_text(stream.getvalue(), encoding='utf-8')
    (evidence / 'verification.json').write_text(json.dumps({
        'started_at': started.isoformat(),
        'finished_at': datetime.datetime.now().astimezone().isoformat(),
        'tests': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'passed': result.wasSuccessful(),
        'method': 'Automated mouse-coordinate handlers and headless rendering, not human playtesting',
        'levels': metrics,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(stream.getvalue())
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
