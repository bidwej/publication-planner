# Endoscope AI Planning

## Structure
- docs/EndoscopeAI_Publication_Master.md: Master document with cost formulations.
- docs/schedule.md: 12-month schedule overview.
- tests/: Test suite for integrity and scheduling constraints.
- tests/data/: JSON inputs.

## How to Use
1. **Modify** JSON files in `tests/data/`:
   - **config.json**: global parameters (slack window, queue limits, conferences).
   - **conferences.json**: deadlines and dates.
   - **pccp_mods.json**: 17 mods (one per object) with dates, dependencies, and `engineering=true`.
   - **ed_papers.json**: 20 papers with `engineering`, `mod_dependencies`, `dependencies`, `planned_conference` (nullable).
2. **Run** `pytest tests/` to validate before regenerating.
3. **Regenerate** schedule with `docs/schedule.md` by executing this script.

# Endoscope AI Planning – Unified README  
*(updated Jul 2025 & using refactored JSON layout)*  

---

## 1. Overview & Scope  

The **Endoscope AI Plan** schedules  
- **20 Ed Papers** – clinical & engineering research outputs  
- **17 PCCP Mods** – internal engineering milestones (linear)  
- **14 Conferences** – mix of *Engineering* and *Medical* venues, each with distinct abstract/full policies  

> Workflows are distinct but coupled:  
> • PCCP Mods drive some papers via mod‑dependencies  
> • Papers target external conferences under capacity & deadline constraints  

---

## 2. Paper Dependency Graph (20 papers)  

| Chain | Nodes (diagram) | Paper IDs |
|-------|-----------------|-----------|
| Background → UEX → CV | User Exp → CV review | **J1** |a
| Anatomy | MT/IT → NSD → ET | **J2 → J3 → J4** |
| Surface Features | Mid Turb (???) → ET inflamed | **J5 → J6** |
| Path‑Mucus | Mucus → Mucus Bio → Color → Localization | **J7 → J8 → J9 → J10** |
| Path‑Polyps | Polyps → NP vs PCMT → Polyp color | **J11 → J12 → J13** |
| Clinical‑Human | ???? detect → NE (ENT) → NE (PCP) → Gaze | **J14 → J15 → J16 → J17** |
| Lab | Mucus AI vs culture | **J18** |
| CT | CT max → CT eth | **J19 → J20** |

---

## 3. Data Files  

```
data/
 ├─ mods.json          # 17 mods • next_mod pointer
 ├─ papers.json        # 20 papers • parent & mod deps
 └─ conferences.json   # 14 confs • recurrence & deadlines
config.json            # global defaults & file paths
```

### config.json  

```json
{
  "default_paper_lead_time_months": 3,
  "default_mod_lead_time_months": 1,
  "max_concurrent_papers": 2,
  "data_files": {
    "mods": "data/mods.json",
    "papers": "data/papers.json",
    "conferences": "data/conferences.json"
  }
}
```

---

## 4. Conference Types & Venue‑Match Rules  

| Family (examples) | Venue Type | Deadline pattern | Cross‑submission rule |
|-------------------|-----------|------------------|-----------------------|
| ICML, CVPR, MICCAI, NeurIPS | **Engineering** | abstract + full | Engineering papers **OK**; Medical papers **FORBIDDEN** |
| RSNA, SPIE MedImg | **Medical** | full‑only | Both paper types allowed |
| ARS, IFAR, AMIA Inf Summit | **Medical** | abstract‑only | Both paper types allowed |
| AMIA Annual Symp | **Medical** | either | Both paper types allowed |

---

## 5. Key Scheduling Constraints  

* **Mod chain:** linear 1 → 17  
* **Paper→Mod:** start ≥ mod finish + 1 month  
* **Paper→Paper:** start ≥ parent finish + 3 months  
* **Abstract < Full** for dual‑deadline venues  
* **Venue‑type:** Medical papers may *only* go to Medical venues; Engineering papers may go anywhere  
* **Concurrency:** ≤ 2 papers active per month  
* **Draft window:** finish = start + draft_window_months  

---

## 6. Greedy Scheduler Steps  

1. Topological ordering  
2. Earliest feasible month (respect mods, parents, venue window)  
3. Insert abstract & full milestones if required  
4. Shift forward to satisfy capacity  

---

## 7. Annual Summary (capacity = 2)  

| Year | Paper Months | Papers Done | Peak C | Avg C | Mod Months |
|-----:|-------------:|------------:|-------:|------:|-----------:|
| 2025 | 5 | 2 | 2 | 0.71 | 2 |
| 2026 | 7 | 2 | 2 | 0.58 | 4 |
| 2027 | 11| 4 | 2 | 0.92 | 6 |
| 2028 | 16| 8 | 2 | 1.33 | 5 |
| 2029 | 8 | 4 | 2 | 1.33 | 1 |

---

## 8. Validation Highlights  

- All IDs resolved (17 mods • 20 papers • 14 confs)  
- Venue‑type rule enforced (no Medical→Engineering submissions)  
- Abstract precedes full where needed  
- Concurrency ≤ 2  
- Tests pass: `pytest -q`  

## Remaining Work

The following tasks remain to be completed:

- Integrate a true ILP optimizer (e.g., using `pulp`) and encode the formal decision variables, constraints, and objective.
- Develop a `src/optimizer.py` module for solving the ILP and exposing solution analysis.
- Write comprehensive unit tests in `tests/test_optimizer.py` to verify optimizer feasibility and objective correctness.
- Populate and verify real-world mod→paper dependencies in `tests/data/ed_papers.json` and `pccp_mods.json`.
- Finalize the mapping of all 14 conferences to deadline dates and eligibility windows in `tests/data/conferences.json`.
- Implement automated Gantt chart generation for visualizing schedules (e.g., via `matplotlib` or `plotly`).
- Validate SlackCost, conference-penalty, and FDA-penalty calculations end-to-end.
- Remove any placeholder or orphan code, and confirm no residual `print` statements or debug artifacts.
- Perform end-to-end testing with real data to confirm schedule feasibility under varying `min_papers_per_month` and `max_papers_per_month`.
- Update the master planning document (`docs/EndoscopeAI_Publication_Master.md`) with finalized constraints and tables.

TODO: replace greedy with scipy.optimize linear programming. We cannot solve because we would like to cross-compile linux binaries for ChatGPT.
TODO: plot each plausible thing and be able to interacivly hit a key to see next one or save which would save everyting to json so need funcs for this.

import numpy as np
import matplotlib.pyplot as plt

# Data for the chart based on previous LP solution
tasks = ["Mod1", "Mod2", "Paper1", "Paper2"]
start = [1, 2, 2, 3]
duration = [1, 1, 3, 3]

# Prepare plot
fig, ax = plt.subplots(figsize=(8, 3))

for i, (task, s, d) in enumerate(zip(tasks, start, duration)):
    ax.barh(y=i, width=d, left=s, height=0.5, align='center', edgecolor='black')

ax.set_yticks(range(len(tasks)))
ax.set_yticklabels(tasks)
ax.set_xlabel("Month")
ax.set_title("Plausible Schedule Gantt Chart (Matplotlib)")

plt.tight_layout()

# Display inline PNG
import io
import PIL.Image

buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
im = PIL.Image.open(buf)
im.show()

# To display directly in the notebook (chat) output:
import IPython.display as display
display.display(im)

plt.close()

# Endoscope AI Planning

EdPlan helps plan publication schedules for endoscopy AI papers, ensuring:
- Mod readiness is respected
- Papers do not overlap beyond concurrency limits
- Abstracts precede full papers
- Deadlines for conferences are met

---

## ✅ What EdPlan CAN Do

✅ Greedy scheduling:
- Always generates a valid schedule
- Respects:
  - mod deadlines
  - parent-child paper chains
  - concurrency limits
- Provides:
  - Monthly tables
  - Markdown summaries
  - Gantt charts

✅ LP Relaxation (analysis only):
- Detects impossible constraints
- Provides approximate earliest-start bounds

✅ Plot Gantt charts:
- Bars for full papers
- Diamonds for abstracts

---

## ❌ What EdPlan CANNOT Do

❌ No guaranteed optimal schedule:
- Without ILP solvers (e.g. CBC, Gurobi), we cannot minimize cost or time exactly
- LP relaxation cannot enforce integer constraints

❌ No automatic binary installs:
- Platforms like ChatGPT cannot run binary solvers

---

## How to Use

### 1. Edit Data Files
- `config.json`
- `data/mods.json`
- `data/papers.json`
- `data/conferences.json`

### 2. Run Greedy Schedule

```python
from src.loader import load_config
from src.planner import Planner
from src.plot import plot_schedule

cfg = load_config("config.json")
planner = Planner(cfg)

mod_sched, paper_sched = planner.greedy_schedule()

rows = planner.generate_monthly_table()

plot_schedule(mod_sched, paper_sched, cfg)
```

### 3. Optional LP Relaxation

```python
from src.optimizer import solve_lp

mod_sched_lp, paper_sched_lp = solve_lp(cfg)
```

---

## Remaining Work

- Optional integration of external ILP solvers (future)
- Testing LP vs greedy discrepancies
- Interactive Gantt charts
