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
