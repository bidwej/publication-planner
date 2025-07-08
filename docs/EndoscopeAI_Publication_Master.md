
# EndoscopeAI Publication‑Planning Master Document  
*(Working draft – Jul 03 2025)*  

This single document consolidates every element we need to build and eventually solve a **constrained, linear‑optimization schedule** for EndoscopeAI publications and PCCP software releases.  
It now reflects **all clarifications from our conversation through Jul 03 2025.**



## Change Log  
| Date | Author | Summary |
|------|--------|---------|
| Jul 3 2025 | ChatGPT | Initial master document created |
| Jul 03 2025 | ChatGPT | • Added soft‑block model for PCCP mods • Added exact “two‑papers‑in‑pipeline” rule • Added capacity analysis and slack strategy • Added penalty variables for late mods |



## 1  PCCP – 48‑Month Update Schedule (fixed order)

*(unchanged; see previous version for full detail)*



## 2  Soft‑Block Model for PCCP Mods

For each mod \(m\):

\[
\textbf{BlockStart}_m \le \text{Finish}_m \le \textbf{BlockEnd}_m + \epsilon + p_m
\]

where  
* **ε** = 1 month free slack  
* \(p_m \ge 0\) incurs penalty cost \(c_m\).




## 3  Concurrency – Papers in Drafting

For each month \(t\) we allow **at least one and at most two** papers to be in their drafting window:

\[
1 \;\le\; \sum_j \mathbf 1\bigl[W_j \le t < S_j\bigr] \;\le\; 2
\]

This keeps the team continuously engaged without over‑loading any subgroup.

## 4  Other Constraints & Objective

* Precedence, data‑ready, abstract lead → unchanged.  
* Objective adds \(\sum_m c_m p_m\) penalties.  




## 5  Capacity & Slack Summary

* Theoretical maximum across 48 months – 32 papers  
* Planned – 20 (Ed) + ≤5 additional ⇒ **≤25** → ~78 % of capacity  
* Result – spare head‑room for new ideas and for pulling pure‑clinical drafts earlier.

## 6  Next‑Step Checklist (revised)

| Task | Owner | Target |
|------|-------|--------|
| Confirm new constraints | Jon & Ed | 10 Jul 2025 |
| Build eligibility matrix \(K_j\) | PM | 15 Jul |
| Encode ILP & run baseline | Data Sci Eng | 22 Jul |
| Review Gantt & adjust | Steering | 31 Jul |



## Appendix A – Ed’s Flow‑Chart Markdown
```markdown
```markdown
flowchart TD
    A["Endoscopic AI Studies<br/>6/7/25"] --> MB["Model Building"]
    A --> CC["Clinical Correlation"]

    MB --> B["<u>Background</u>"]
    MB --> D["<u>Anatomy</u>"] 
    MB --> SF["<u>Surface Features</u>"]
    MB --> P["<u>Pathology</u>"]

    B --> UEX["User Experience (UEX)<br/>paper survey"]
    UEX --> CV["Computer Vision (CV)<br/>endoscopy review"]

    D --> MT1["Middle Turbinate/<br/>Inferior Turbinate<br/>(MT/IT)"]
    MT1 --> NSD["Nasal Septal<br/>Deviation<br/>(NSD)"]
    NSD --> ET1["Eustachian Tube<br/>(ET)"]

    SF --> MT2["Middle Turbinate<br/>(MT ???/???)"]
    MT2 --> ET2["Eustachian Tube (ET)<br/>inflamed vs ETDQ"]

    P --> M["Mucus"]
    P --> PO["Polyps"]
    M --> MB1["Mucus Biology"]
    PO --> NP["Nasal Polyps (NP) vs<br/>PCMT"]
    MB1 --> C["Color"]
    NP --> PC["Polyp color"]
    C --> L["Localization<br/>(NC Mapping)"]

    CC --> H["<u>Human</u>"]
    CC --> LAB["<u>Lab</u>"]
    CC --> CT["<u>Computed Tomography (CT)</u>"]

    H --> DD["???? detection<br/>(vs Medical Doctor (MD))"]
    DD --> NE1["Nasal Endoscopy (NE)<br/>AI Clinical Decision<br/>Support (CDS) vs panel<br/>| ENT"]
    NE1 --> NE2["Nasal Endoscopy (NE)<br/>AI Clinical Decision<br/>Support (CDS) vs panel<br/>| PCP"]
    NE2 --> ST["Gaze tracking<br/>vs AI"]

    LAB --> MA["Mucus AI<br/>vs culture"]

    CT --> CT1["CT max vs NE<br/>Maxillary Mucosa<br/>(MM) | Maxillary"]
    CT1 --> CT2["CT eth vs NE<br/>Middle Turbinate<br/>(MT) | Ethmoid"]

    classDef rootNode fill:#e1f5fe,stroke:#01579b,stroke-width:3px
    classDef mainCategory fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef subCategory fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef process fill:#fff3e0,stroke:#e65100,stroke-width:2px

    class A rootNode
    class MB,CC mainCategory
    class B,D,SF,P,H,LAB,CT subCategory
    class UEX,MT1,MT2,M,PO,DD,MA,CT1,CV,NSD,ET1,ET2,MB1,NP,C,PC,L,NE1,NE2,ST,CT2 process

### Main Summary
| Level 2 Category           | Details Table               | # Papers |
| -------------------------- | --------------------------- | -------- |
| MB (Model Building)        | [Table 1: MB Details](#table-1-mb-details) | 13       |
| CC (Clinical Correlation)  | [Table 2: CC Details](#table-2-cc-details) | 7        |
| **Grand Total**            |                             | **20**   |

---

### Table 1: MB Details {#table-1-mb-details}
| Node Path (IDs)         | Full Path (Names)                                                                                      | # Papers |
| ----------------------- | ------------------------------------------------------------------------------------------------------ | -------- |
| B → UEX → CV            | Background → User Experience (UEX paper survey) → Computer Vision (CV endoscopy review)               | 1        |
| D → MT1 → NSD → ET1     | Anatomy → Middle Turbinate/Inferior Turbinate (MT/IT) → Nasal Septal Deviation (NSD) → Eustachian Tube (ET) | 3        |
| SF → MT2 → ET2          | Surface Features → Middle Turbinate (MT ???/???) → Eustachian Tube (ET inflamed vs ETDQ)               | 2        |
| P → M → MB1 → C → L     | Pathology → Mucus → Mucus Biology → Color → Localization (NC Mapping)                                    | 4        |
| P → PO → NP → PC        | Pathology → Polyps → Nasal Polyps (NP) vs PCMT → Polyp color                                           | 3        |

---

### Table 2: CC Details {#table-2-cc-details}
| Node Path (IDs)               | Full Path (Names)                                                                                                                                                         | # Papers |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| H → DD → NE1 → NE2 → ST        | Human → ???? detection (vs Medical Doctor (MD)) → Nasal Endoscopy (NE) AI Clinical Decision Support (CDS) vs panel &#124; ENT → Nasal Endoscopy (NE) AI Clinical Decision Support (CDS) vs panel &#124; PCP → Gaze tracking vs AI | 4        |
| LAB → MA                      | Lab → Mucus AI vs culture                                                                                                                                                 | 1        |
| CT → CT1 → CT2                | Computed Tomography (CT) → CT max vs NE Maxillary Mucosa (MM) &#124; Maxillary → CT eth vs NE Middle Turbinate (MT) &#124; Ethmoid                                    | 2        |
```
```


---

## NEW: PCCP Soft Block Constraints

Although Mods 1–17 have planned completion phases (e.g. Phase 1 = months 1–6), they are not hard deadlines.
Instead, the optimizer models these as “soft blocks”:

- **Mods may slip ± 2 months** without large penalty.
- Slipping beyond the block incurs a time penalty in the objective.
- Papers depending on a Mod cannot start drafting until the Mod is validated.

Mathematically:

\[
S_j \ge R_j + \delta_{\text{slip}}
\]

where \( \delta_{\text{slip}} \) is a decision variable penalized in the objective if positive.

---


## NEW: Target Pipeline Coverage (1–2 Papers Active)

The scheduler **aims for two** overlapping drafts whenever possible, but maintains a safe range of **1–2**:

\[
1 \le \sum_{j} y_{j,t} \le 2 \quad \forall t
\]

We model
* **Standard paper**: 3‑month drafting window  
* **Fast paper** (e.g. abstract‑only): 1‑month drafting window

## NEW: Paper Load Capacity

Estimated paper capacity over 48 months:

- Standard load: ~16 papers per year
- Max capacity (2 concurrent x 12 months / 3 months): ~32 papers total

Current plan:
- Ed’s 20 papers
- ~5–10 additional possible papers if desired

Therefore, **we have spare capacity** and can consider adding papers or moving Ed’s purely clinical papers earlier.

---

## NEW: Purely Clinical Papers May Move Earlier

Some Ed papers (e.g. User Experience, Gaze Tracking) do not depend on model outputs and can be scheduled earlier:

Examples:
- J1 – CV Endoscopy Review
- J9 – Color Analysis
- J17 – Gaze Tracking

The optimizer should assign these earlier if pipeline gaps exist.

---

## NEW: Conference Mapping for Ed’s Papers

| Paper | Likely Venues |
|-------|---------------|
| J1 | ICML, MIDL, CVPR |
| J2 | MICCAI, ARS |
| J3 | MICCAI, ARS |
| J4 | MICCAI, ARS |
| J5 | MICCAI, ARS |
| J6 | MICCAI, ARS |
| J7 | ARS, IFAR |
| J8 | ARS, IFAR |
| J9 | CVPR, MIDL |
| J10 | MICCAI |
| J11 | MICCAI, ARS |
| J12 | MICCAI, ARS |
| J13 | MICCAI, ARS |
| J14 | AMIA, MICCAI |
| J15 | AMIA, ARS |
| J16 | AMIA, ARS |
| J17 | CVPR, AMIA |
| J18 | IFAR, ARS |
| J19 | RSNA, SPIE |
| J20 | RSNA, SPIE |

This helps the optimizer choose among venues when scheduling each paper.

---


## Unified Slack‑Cost Formulation

\[
\text{SlackCost}_j =
P_j\,(S_j - S_{j,\text{earliest}}) + Y_j\,\mathbf 1_{\text{year‑deferred}} + A_j\,\mathbf 1_{\text{abstract‑miss}}
\]

| Coefficient | Default \$ | Notes |
|-------------|-----------:|-------|
| \(P_j\) | 1 000 per month (3 000 for J19–J20) | Monthly slip |
| \(Y_j\) | 5 000 (10 000 for J19–J20) | Full‑year deferral |
| \(A_j\) | 3 000 | Missed abstract‑only window (ARS / RSNA) |

## Clarifications Added

- Mods may finish earlier or later than planned.
- Paper submission is intentionally decoupled from mod finish dates for strategic conference timing.
- The optimizer decides paper months — there is no fixed month-by-month plan for papers 1–20.

---

## NEW: Next Steps Checklist (Updated)

| Task | Owner | Due |
|------|-------|-----|
| Approve updated ILP constraints & variables | Jon & Ed | 10 July 2025 |
| Populate conference eligibility matrix (K_j) | Data Sci PM | 15 July 2025 |
| Review pipeline load vs capacity | PI Group | 18 July 2025 |
| Run initial ILP optimization | Ops Team | 25 July 2025 |
| Confirm conference abstracts for Fall/Winter | All | 1 Aug 2025 |

---


---

## NEW: Gantt Chart Visualization

To help visualize the plan, we propose generating a **Gantt chart** showing:

- Planned PCCP mod finish windows (with soft block shading)
- Data-ready milestones for each paper
- Paper drafting windows (highlighting overlapping drafts)
- Conference deadlines

Tools we can use:

- Python matplotlib
- Plotly Gantt charts
- Excel timelines

Each paper block can be color-coded:

- Engineering-heavy papers → blue
- Clinical or survey papers → green
- Abstract-only → orange

This will help spot gaps in coverage and concurrency overload.

---

## Clarification: FDA vs. Paper Submissions

A key principle:

> **Mod completion and regulatory (FDA) submission may happen before scientific paper submission.**

- The optimizer allows papers to lag weeks or months after a Mod finishes.
- This ensures we can align publications with conference schedules or strategic timing.
- Regulatory compliance remains on its own timeline.

We intentionally decouple publication dates from regulatory filings.

---


---



## 7A  Mod → Conference Alignment

**Purpose:** provide a quick lookup of which major conference windows best match each PCCP modification once its validation data are locked.

| Mod | Title (short) | Phase | Data‑Ready (est.) | Earliest Candidate Conference Windows* |
|----:|---------------|-------|-------------------|-----------------------------------------|
| 1 | Samurai Automated 2D | Phase 1 | Jun 2025 | SPIE MI 2026, EMBC 2026 |
| 2 | Samurai Manual‑Verified 2D | Phase 1 | Jun 2025 | SPIE MI 2026, EMBC 2026 |
| 3 | SLAM Infrastructure | Phase 2 | Jun 2026 | MICCAI 2026, CVPR 2026 |
| 4 | Bayesian Evidence | Phase 2 | Jun 2026 | MICCAI 2026, CVPR 2026 |
| 5 | Coverage Visualization | Phase 2 | Jun 2026 | MICCAI 2026, CVPR 2026 |
| 6 | SLAM 3‑D Label Tracking | Phase 2 | Jun 2026 | MICCAI 2026, CVPR 2026 |
| 7 | Polyp Instance Counting | Phase 3 | Jun 2027 | MICCAI 2027, ARS 2027 |
| 8 | Polyp Size Measurement | Phase 3 | Jun 2027 | MICCAI 2027, ARS 2027 |
| 9 | Swelling Detection | Phase 3 | Jun 2027 | MICCAI 2027, ARS 2027 |
| 10 | Septal Deviation | Phase 3 | Jun 2027 | MICCAI 2027, ARS 2027 |
| 11 | Septal Perforation | Phase 3 | Jun 2027 | MICCAI 2027, ARS 2027 |
| 12 | Evidence Sufficiency | Phase 3 | Jun 2027 | MICCAI 2027, ARS 2027 |
| 13 | CT Registration | Phase 4 | Jun 2028 | RSNA 2028, SPIE MI 2029 |
| 14 | CT Auto‑Label Back‑proj | Phase 4 | Jun 2028 | RSNA 2028, SPIE MI 2029 |
| 15 | SLAM Manual‑3D Verify | Phase 4 | Jun 2028 | RSNA 2028, SPIE MI 2029 |
| 16 | CT Manual‑3D Verify | Phase 4 | Jun 2028 | RSNA 2028, SPIE MI 2029 |
| 17 | IMU‑Enhanced Tracking | Phase 5 | Dec 2028 | ICRA 2029, MICCAI 2029 |

*Final venue is chosen by the optimizer after checking draft capacity, paper precedence, and SlackCost penalties.


## 8  Conference Catalogue & 2025 Deadlines  (updated)

| Conference | Full Papers Accepted? | Abstract Required? | **Full‑Paper Deadline** | **Abstract / Intent Deadline** | Conference Timing |
|------------------------------------|--------------------|-------------------------|--------------------------------|-----------------------------------------------|----------------|
| **ICML (Machine Learning)** | Yes | Yes | 30 Jan 2025 (AoE) | 23 Jan 2025 (AoE) | July 2025 |
| **MIDL (Medical Imaging with Deep Learning)** | Yes | Yes | 31 Jan 2025 (AoE) | 17 Jan 2025 (AoE) | July 2025 |
| **MICCAI (Medical Imaging & AI)** | Yes | Yes | 27 Feb 2025 (AoE) | 13 Feb 2025 (AoE) | Oct 2025 |
| **EMBC (Biomedical Engineering)** | Yes | No | 9 Feb 2025 | N/A | July 2025 |
| **ICCV (Computer Vision, biennial)** | Yes | Yes | 7 Mar 2025 23:59 HST | 3 Mar 2025 23:59 HST | Oct 2025 (biennial) |
| **AMIA Annual Symposium** | Yes | No | 25 Mar 2025 | N/A | Nov 2025 |
| **ARS (American Rhinologic Society)** | No (abstract‑only) | Yes | N/A | 4 Apr 2025 | Fall / Spring |
| **NeurIPS (AI / ML)** | Yes | Yes | 15 May 2025 (AoE) | 11 May 2025 (AoE) | Dec 2025 |
| **RSNA (Radiology)** | No (abstract‑only) | Yes | N/A | 7 May 2025 12:00 CT | Nov / Dec 2025 |
| **SPIE Medical Imaging** | Yes (camera‑ready) | Yes | 28 Jan 2026 | 6 Aug 2025 | Feb 2026 |
| **IFAR (Intl. Forum of Allergy & Rhinology)** | Optional post‑conf | Yes | 31 Dec 2025 (manuscript opt.) | 8 Aug 2025 | Mar 2026 |
| **ICRA (Robotics & Automation)** | Yes | No | 15 Sep 2024 23:59 PST | N/A | May 2025 |
| **AMIA Informatics Summit** | No (abstract‑only) | Yes | N/A | 17 Sep 2024 23:59 EDT | Mar 2025 |
| **CVPR (Computer Vision)** | Yes | Yes | 15 Nov 2024 23:59 PT | 8 Nov 2024 23:59 PT | Jun 2025 |

*Deadlines roll forward one calendar year for 2026–2029; ICCV runs biennially (2025, 2027, 2029).*


## 9  Conference‑Eligibility Sets \(K_j\)

The optimizer needs an **explicit eligibility set** \(K_j\) of conference deadlines for each paper.  
These were implicit in earlier tables; here they are formalised:

| Paper | Eligibility \(K_j\) (Conference Families) |
|-------|-------------------------------------------|
| J1 | {ICML, MIDL, CVPR, NeurIPS} |
| J2 | {MICCAI, ARS, IFAR} |
| J3 | {MICCAI, ARS, IFAR} |
| J4 | {MICCAI, ARS, IFAR} |
| J5 | {MICCAI, ARS, IFAR} |
| J6 | {MICCAI, ARS, IFAR} |
| J7 | {ARS, IFAR, AMIA} |
| J8 | {ARS, IFAR, AMIA} |
| J9 | {CVPR, MIDL, NeurIPS} |
| J10| {MICCAI, CVPR} |
| J11| {MICCAI, ARS, IFAR} |
| J12| {MICCAI, ARS, IFAR} |
| J13| {MICCAI, ARS, IFAR} |
| J14| {AMIA Annual, MICCAI} |
| J15| {AMIA Annual, ARS, IFAR} |
| J16| {AMIA Annual, ARS, IFAR} |
| J17| {CVPR, AMIA Annual} |
| J18| {IFAR, ARS} |
| J19| {RSNA, SPIE Med Imaging} |
| J20| {RSNA, SPIE Med Imaging} |

\(K_j\) lists *families*; each family contains a yearly deadline instance \(k\). The solver expands \(k\) across years 2025‑2029.

---


## 10  Mod‑to‑Mod Precedence  (clarified)

All PCCP mods follow their numeric order.  
Two **explicit technical dependencies** must also be respected:

| From Mod | To Mod | Reason |
|----------|--------|--------|
| 3 | 4 | Bayesian evidence logic requires SLAM poses |
| 4 | 5 | Coverage guidance consumes Bayesian confidences |

No other additional precedence constraints are presently defined.

## 
## 12  Conference‑Preference Weights

To discourage ill‑matched venue choices we introduce a **venue‑type penalty matrix**:

| Paper Type | Venue Type | Penalty \$ | Rationale |
|------------|-----------:|-----------:|-----------|
| Engineering‑heavy | Clinical/ENT abstract‑only | 3000 | Loss of technical audience |
| Clinical | Engineering (ICML/CVPR) | 1500 | Audience mis‑match |
| Full‑paper capable | Abstract‑only venue | 2000 | Reduces publication depth |
| Good match | Good match | 0 | — |

This penalty is **added to SlackCost** in the objective.

---

## 13  Reviewer & Regulatory Delays

Reviewer or FDA feedback delays are **modeled as stochastic slack**:  
– mean = 1 month, σ = 1 month.  
A buffer of **+1 month** is added to drafting windows.

---

## 14  Gantt Chart Placeholder

A prototype Gantt (not shown here) will plot:

* Grey bands → PCCP phase blocks (with soft margins)  
* Green markers → Data‑ready dates \(R_j\)  
* Blue bars → paper drafting windows  
* Red diamonds → conference deadlines

Generation planned via `plotly.express.timeline` in the optimisation notebook.

---



## 16  Rolling Optimisation Cadence

Re‑solve the ILP **quarterly** *or* if any trigger occurs:

1. Any Mod slips > 2 months beyond its block end.  
2. Any paper misses its chosen deadline.  
3. Resource allocation changes (e.g. new FTE joins/leaves).

---

## 17  Mod → FDA → Publication Lead‑Time

We ensure at least **0 months gap** (i.e. can be simultaneous) between:

* Mod finish → FDA submission  
* FDA submission → paper drafting start

If future policy requires a lag (e.g. embargo), add:

\[
S_{\text{FDA},m} + \tau_{\text{embargo}} \le S_j
\]

where default \(\tau_{\text{embargo}} = 0\).

---

## Appendix B — Ed’s Study Flowchart (Markdown)

```markdown
flowchart TD
    A["Endoscopic AI Studies<br/>6/7/25"] --> MB["Model Building"]
    A --> CC["Clinical Correlation"]
    MB --> B["<u>Background</u>"]
    MB --> D["<u>Anatomy</u>"]
    MB --> SF["<u>Surface Features</u>"]
    MB --> P["<u>Pathology</u>"]
    B --> UEX["User Experience (UEX)<br/>paper survey"]
    UEX --> CV["Computer Vision (CV)<br/>endoscopy review"]
    D --> MT1["Middle Turbinate/<br/>Inferior Turbinate<br/>(MT/IT)"]
    MT1 --> NSD["Nasal Septal<br/>Deviation<br/>(NSD)"]
    NSD --> ET1["Eustachian Tube<br/>(ET)"]
    SF --> MT2["Middle Turbinate<br/>(MT ???/???)"]
    MT2 --> ET2["Eustachian Tube (ET)<br/>inflamed vs ETDQ"]
    P --> M["Mucus"]
    P --> PO["Polyps"]
    M --> MB1["Mucus Biology"]
    PO --> NP["Nasal Polyps (NP) vs<br/>PCMT"]
    MB1 --> C["Color"]
    NP --> PC["Polyp color"]
    C --> L["Localization<br/>(NC Mapping)"]
    CC --> H["<u>Human</u>"]
    CC --> LAB["<u>Lab</u>"]
    CC --> CT["<u>Computed Tomography (CT)</u>"]
    H --> DD["???? detection<br/>(vs Medical Doctor (MD))"]
    DD --> NE1["Nasal Endoscopy (NE)<br/>AI Clinical Decision<br/>Support (CDS) vs panel<br/>| ENT"]
    NE1 --> NE2["Nasal Endoscopy (NE)<br/>AI Clinical Decision<br/>Support (CDS) vs panel<br/>| PCP"]
    NE2 --> ST["Gaze tracking<br/>vs AI"]
    LAB --> MA["Mucus AI<br/>vs culture"]
    CT --> CT1["CT max vs NE<br/>Maxillary Mucosa<br/>(MM) | Maxillary"]
    CT1 --> CT2["CT eth vs NE<br/>Middle Turbinate<br/>(MT) | Ethmoid"]
    classDef rootNode fill:#e1f5fe,stroke:#01579b,stroke-width:3px
    classDef mainCategory fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef subCategory fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef process fill:#fff3e0,stroke:#e65100,stroke-width:2px
    class A rootNode
    class MB,CC mainCategory
    class B,D,SF,P,H,LAB,CT subCategory
    class UEX,MT1,MT2,M,PO,DD,MA,CT1,CV,NSD,ET1,ET2,MB1,NP,C,PC,L,NE1,NE2,ST,CT2 process
```

---


---

## 18  Drafting Windows by Paper

Below are estimated drafting times for each paper:

| J‑ID | Title | Drafting Window (months) |
|------|-----------------------------------|--------------------------|
| J1 | Computer Vision (CV) endoscopy review | 2 |
| J2 | Middle Turbinate/Inferior Turbinate (MT/IT) | 3 |
| J3 | Nasal Septal Deviation (NSD) | 3 |
| J4 | Eustachian Tube (ET) | 3 |
| J5 | Middle Turbinate (MT ???/???) | 2 |
| J6 | Eustachian Tube (ET inflamed vs ETDQ) | 2 |
| J7 | Mucus | 2 |
| J8 | Mucus Biology | 2 |
| J9 | Color | 1 |
| J10 | Localization (NC Mapping) | 3 |
| J11 | Polyps | 3 |
| J12 | Nasal Polyps (NP) vs PCMT | 2 |
| J13 | Polyp color | 1 |
| J14 | ???? detection (vs Medical Doctor (MD)) | 3 |
| J15 | Nasal Endoscopy (NE) AI CDS vs ENT panel | 3 |
| J16 | Nasal Endoscopy (NE) AI CDS vs PCP panel | 3 |
| J17 | Gaze tracking vs AI | 2 |
| J18 | Mucus AI vs culture | 2 |
| J19 | CT max vs NE Maxillary Mucosa (MM) | 3 |
| J20 | CT eth vs NE Middle Turbinate (MT) | 3 |

Default: Engineering papers = 3 months, Clinical surveys = 1–2 months.

---

## 19  Slack Costs for Abstract-Only Venues

Missing an abstract-only venue (e.g. ARS) incurs \$3,000 penalty plus one-year deferral cost.

---

## 20  Biennial Conference Clarification

**ICCV** is biennial, available only in odd-numbered years (2025, 2027, etc.). The optimizer skips ICCV for even years.

---

## 21  Paper-to-Paper Lead Times

Some paper pairs require faster or slower leads:

| Parent Paper | Child Paper | Lead Time (months) |
|--------------|-------------|--------------------|
| J11 | J12 | 1 |
| J12 | J13 | 1 |
| J19 | J20 | 2 |

Default for all others = 3 months.

---

## 22  Slack Cost for Missing Annual Window

SlackCost accounts for forced deferral to the next year:

\[
\text{SlackCost}_j = \text{BasePenalty} + \text{YearDelayCost}
\]

Estimated YearDelayCost = \$5,000 per missed cycle.

---

## 23  PCCP Mod-to-Mod Dependencies

While mods follow sequential order, known dependencies include:

| From Mod | To Mod | Dependency? |
|----------|--------|-------------|
| 3 | 4 | Yes |
| 4 | 5 | Yes |

All other mods assumed sequential but independent unless future design states otherwise.

---

## 24  Dummy Gantt Example

```
|----------------|-------------------------------|
| Mod 3          | ██████████████                |
| Mod 4          |            ███████████        |
| Paper J10      |                    ███        |
| Paper J11      |                          ███  |
| Conference MICCAI Deadline |               ▲   |
|----------------|-------------------------------|
Months:         1    6    12    18    24    30
```

This is only a schematic layout.

---

## 25  Master Paper Details Table

| J-ID | Title | Data Ready | Drafting Window | K_j Venues | Parent Papers |
|------|---------------------------------|------------|-----------------|-----------------|-----------------|
| J1 | Computer Vision (CV) endoscopy review | Jun 2025 | 2 | ICML, MIDL, CVPR | - |
| J2 | Middle Turbinate/Inferior Turbinate (MT/IT) | Jun 2026 | 3 | MICCAI, ARS, IFAR | - |
| J3 | Nasal Septal Deviation (NSD) | Jun 2027 | 3 | MICCAI, ARS, IFAR | J2 |
| J4 | Eustachian Tube (ET) | Jun 2027 | 3 | MICCAI, ARS, IFAR | J3 |
| J5 | Middle Turbinate (MT ???/???) | Jun 2027 | 2 | MICCAI, ARS, IFAR | - |
| J6 | Eustachian Tube (ET inflamed vs ETDQ) | Jun 2027 | 2 | MICCAI, ARS, IFAR | J5 |
| J7 | Mucus | Jun 2027 | 2 | ARS, IFAR, AMIA | - |
| J8 | Mucus Biology | Jun 2027 | 2 | ARS, IFAR, AMIA | J7 |
| J9 | Color | Jun 2027 | 1 | CVPR, MIDL, NeurIPS | J8 |
| J10 | Localization (NC Mapping) | Jun 2026 | 3 | MICCAI, CVPR | J9 |
| J11 | Polyps | Jun 2027 | 3 | MICCAI, ARS, IFAR | - |
| J12 | Nasal Polyps (NP) vs PCMT | Jun 2027 | 2 | MICCAI, ARS, IFAR | J11 |
| J13 | Polyp color | Jun 2027 | 1 | MICCAI, ARS, IFAR | J12 |
| J14 | ???? detection (vs MD) | Jun 2027 | 3 | AMIA, MICCAI | - |
| J15 | NE AI CDS vs ENT panel | Jun 2027 | 3 | AMIA, ARS, IFAR | J14 |
| J16 | NE AI CDS vs PCP panel | Jun 2027 | 3 | AMIA, ARS, IFAR | J15 |
| J17 | Gaze tracking vs AI | Jun 2027 | 2 | CVPR, AMIA | J16 |
| J18 | Mucus AI vs culture | Aug 2027 | 2 | IFAR, ARS | - |
| J19 | CT max vs NE Maxillary | Jul 2028 | 3 | RSNA, SPIE | - |
| J20 | CT eth vs NE MT | Jul 2028 | 3 | RSNA, SPIE | J19 |

---

## 26  Scenario Example

> “If Mod 10 slips from June to August 2027, J3 and J4 must defer to MICCAI 2028, adding a \$2,000 SlackCost each. Meanwhile, papers J11 and J12 proceed, keeping concurrency at 2. No downstream pipeline gaps occur.”

---



---


## 3  Concurrency – Papers in Drafting

For each month \(t\) we allow **at least one and at most two** papers to be in their drafting window:

\[
1 \;\le\; \sum_j \mathbf 1\bigl[W_j \le t < S_j\bigr] \;\le\; 2
\]

This keeps the team continuously engaged without over‑loading any subgroup.


## 
## Single‑Conference Submission Policy

Each paper is submitted to **one venue per annual cycle**.  
If the deadline is missed, the optimizer automatically retargets the next compatible venue in a subsequent cycle; simultaneous multi‑submission is prohibited.

## Conference Cycles Clarification

All conferences repeat annually **except ICCV**, which is biennial (only odd-numbered years).

---

## Paper-to-Paper Lead Times (Unified Statement)

All paper-to-paper lead times Δ are paper-specific:

- Default = 3 months
- Exceptions listed in Section 21

This replaces prior single Δ references.

---


## 10  
## Venue Penalty Matrix (Unified Table)

| Paper Type | Venue Type | Penalty \$ |
|------------|------------|-----------:|
| Engineering-heavy | Clinical abstract-only | 3000 |
| Clinical | Engineering venue | 1500 |
| Full paper capable | Abstract-only venue | 2000 |
| Good match | Good match | 0 |

These penalties are added to SlackCost in the objective.

---


## Gantt Chart Note

The ASCII block in §24 is **illustrative only**.  
Actual timelines will be generated **after solving the ILP** using Python (Plotly or Matplotlib).

## Merged K_j Sets Into Master Table

Below is the **unified master table** including conference eligibility:

| J-ID | Title | Data Ready | Draft Window | K_j Venues | Parent Papers | P_j | Y_j |
|------|-------|------------|--------------|------------|---------------|-----|-----|
| J1 | Computer Vision (CV) endoscopy review | Jun 2025 | 2 | ICML, MIDL, CVPR, NeurIPS | - | 1000 | 5000 |
| J2 | Middle Turbinate/Inferior Turbinate (MT/IT) | Jun 2026 | 3 | MICCAI, ARS, IFAR | - | 1000 | 5000 |
| J3 | Nasal Septal Deviation (NSD) | Jun 2027 | 3 | MICCAI, ARS, IFAR | J2 | 1000 | 5000 |
| J4 | Eustachian Tube (ET) | Jun 2027 | 3 | MICCAI, ARS, IFAR | J3 | 1000 | 5000 |
| J5 | Middle Turbinate (MT ???/???) | Jun 2027 | 2 | MICCAI, ARS, IFAR | - | 1000 | 5000 |
| J6 | Eustachian Tube (ET inflamed vs ETDQ) | Jun 2027 | 2 | MICCAI, ARS, IFAR | J5 | 1000 | 5000 |
| J7 | Mucus | Jun 2027 | 2 | ARS, IFAR, AMIA | - | 1000 | 5000 |
| J8 | Mucus Biology | Jun 2027 | 2 | ARS, IFAR, AMIA | J7 | 1000 | 5000 |
| J9 | Color | Jun 2027 | 1 | CVPR, MIDL, NeurIPS | J8 | 1000 | 5000 |
| J10 | Localization (NC Mapping) | Jun 2026 | 3 | MICCAI, CVPR | J9 | 1000 | 5000 |
| J11 | Polyps | Jun 2027 | 3 | MICCAI, ARS, IFAR | - | 1000 | 5000 |
| J12 | Nasal Polyps (NP) vs PCMT | Jun 2027 | 2 | MICCAI, ARS, IFAR | J11 | 1000 | 5000 |
| J13 | Polyp color | Jun 2027 | 1 | MICCAI, ARS, IFAR | J12 | 1000 | 5000 |
| J14 | ???? detection (vs MD) | Jun 2027 | 3 | AMIA, MICCAI | - | 1000 | 5000 |
| J15 | NE AI CDS vs ENT panel | Jun 2027 | 3 | AMIA, ARS, IFAR | J14 | 1000 | 5000 |
| J16 | NE AI CDS vs PCP panel | Jun 2027 | 3 | AMIA, ARS, IFAR | J15 | 1000 | 5000 |
| J17 | Gaze tracking vs AI | Jun 2027 | 2 | CVPR, AMIA | J16 | 1000 | 5000 |
| J18 | Mucus AI vs culture | Aug 2027 | 2 | IFAR, ARS | - | 1000 | 5000 |
| J19 | CT max vs NE Maxillary Mucosa (MM) | Jul 2028 | 3 | RSNA, SPIE | - | 3000 | 10000 |
| J20 | CT eth vs NE Middle Turbinate (MT) | Jul 2028 | 3 | RSNA, SPIE | J19 | 3000 | 10000 |

---

## Scenario Note (clarified)

> “If Mod 10 slips by 2 months, J3 and J4 shift to MICCAI 2028. Each incurs \$2,000 SlackCost. However, papers J11 and J12 continue as planned, maintaining concurrency at ~2 papers and avoiding gaps.”

---

All prior sections are **retained unchanged below these updates.**


### Addendum

- **Conferences**: There are **14** conferences in total that must be scheduled.
- **Ed’s Papers**:
  - **Total papers**: 20
  - **Queue constraints**: Always maintain **1 ≤ #papers in queue ≤ 2**
  - **Temporal constraint**: Each publication may have both an **abstract** and a **full paper**, so the abstract **must** be submitted *before* the full paper; their submission windows must not overlap.
- **Mods**: 17 modules in the PCCP plan remain on a flexible timeline for publication dates.

<!-- ADDENDUM START -->
### Addendum

- **Conferences**: There are **14** conferences in total that must be scheduled.
- **Ed’s Papers**:
  - **Total papers**: 20
  - **Queue constraints**: Always maintain **1 ≤ #papers in queue ≤ 2**
  - **Temporal constraint**: Each publication may have both an **abstract** and a **full paper**, so the abstract **must** be submitted *before* the full paper; their submission windows must not overlap.
- **Mods**: 17 modules in the PCCP plan remain on a flexible timeline for publication dates.
<!-- ADDENDUM END -->

### Mod Scheduling Flexibility and Costs

- **Mod Delivery Windows**: Each module (1–17) has an **ideal submission date** with a **±1 month (30 days)** window of low cost.
- **SlackCost** for module *j*:
  \[
    	ext{SlackCost}_j = \max(0,\; |D_{	ext{actual},j} - D_{	ext{ideal},j}| - 30)
  \]
  where dates are in days; costs accrue linearly beyond the 30-day window.
- **High Cost Function**: Deviations within ±30 days incur **zero** cost; beyond that, cost = number of days outside the window.
