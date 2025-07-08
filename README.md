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

