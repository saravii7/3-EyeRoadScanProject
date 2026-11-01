"""±20 % sensitivity check of the priority weights (Technical report, Section 4.4).

Part 1: the three worked examples in src/priority.py.
Part 2: 200 randomly generated reports (seed 42, 1 to 6 boxes, realistic class mix):
Spearman correlation, largest rank shift, top-10 overlap and band changes per weight change.
Run from the repository root:  python scripts/priority_sensitivity.py
"""
import random
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from priority import WEIGHTS, priority_score  # noqa: E402

W, H = 1000, 500
EXAMPLES = {
    "A thin crack": [{"cls": "D00", "x": 0, "y": 0, "w": 100, "h": 100, "conf": 0.6}],
    "B one pothole": [{"cls": "D40", "x": 0, "y": 0, "w": 250, "h": 200, "conf": 0.9}],
    "C five potholes": [{"cls": "D40", "x": 0, "y": 0, "w": 173, "h": 173, "conf": 0.95}] * 5,
}
print("base", {k: round(priority_score(v, W, H), 1) for k, v in EXAMPLES.items()})
for k in WEIGHTS:
    for f in (0.8, 1.2):
        w = dict(WEIGHTS); w[k] *= f
        s = {n: round(priority_score(v, W, H, w), 1) for n, v in EXAMPLES.items()}
        print(f"{k} x{f}", s, "order:", sorted(s, key=s.get))

random.seed(42)
reports = []
for _ in range(200):
    dets = []
    for _ in range(random.randint(1, 6)):
        c = random.choice(["D00", "D00", "D10", "D20", "D40"]); side = random.uniform(30, 350)
        dets.append({"cls": c, "x": 0, "y": 0, "w": side, "h": side * random.uniform(.3, 1),
                     "conf": random.uniform(.46, .98)})
    reports.append(dets)
base = np.array([priority_score(r, 1000, 1000) for r in reports]); rb = base.argsort().argsort()
band = lambda x: np.where(x >= 70, 2, np.where(x >= 40, 1, 0))
for k in WEIGHTS:
    for f in (0.8, 1.2):
        w = dict(WEIGHTS); w[k] *= f
        s = np.array([priority_score(r, 1000, 1000, w) for r in reports]); rs = s.argsort().argsort()
        top = len(set(np.argsort(-base)[:10]) & set(np.argsort(-s)[:10]))
        print(f"{k:5s} x{f}: spearman {spearmanr(base, s)[0]:.3f} | max rank shift {abs(rb - rs).max()} "
              f"| top10 kept {top}/10 | band changes {(band(base) != band(s)).sum()}/200")
