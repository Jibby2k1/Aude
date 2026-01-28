# Project Charter — Aude Project

## Contributors
- **Project Lead:** Matty Maloni
- **Primary Contributors:** Raul Valle, Param Gattupalli, Asher Wheatle, Dylan Coben, Gene Mak, Anh Mai
- **Secondary Contributors:** N/A

## Definition
- **Research / Product Question:** Can we beat the current SoTA source separation and location methods?
- **Claim / Hypothesis:** We can via informed models and well-prepared data capturing systems.
- **Novelty:** Model and data collection (3 microphones).
- **Target Venue / Deliverable Context:** IEEE ICASSP
- **Expected Artifacts:**
  - Demo-able hardware for data capture
  - A real-time system
  - A trained, generalizable model

## Delegation (initial)
| Workstream | Owner(s) | Output | Due |
|---|---|---|---|
| Literature review | Matty Maloni, Raul Valle | Paper summary + key baselines (source separation + location) | 2026-02-21 |
| SoTA baselines | Dylan Coben, Param Gattupalli | Reproducible runs + metrics (source separation + location) | 2026-03-21 |
| Data / hardware | Gene Mak, Asher Wheatle | Hardware plan + capture protocol + initial dataset | 2026-03-21 |

## Funding Use
- Budget: TBD
- What we will buy: Hardware (3 microphones + ESP32s)
- Approval process: TBD

## Timeline
- **Weekly meeting time:** Monday 7:30 PM (timezone TBD)
- **Paper draft date (if relevant):** 2026-05-04

### Primary Milestones
| Milestone | Description | Date |
|---|---|---|
| M1 | Review of source separation, location, and hardware details | 2026-02-21 |
| M2 | Capturing data and implementing models | 2026-03-21 |
| M3 | Publishable / demoable results | 2026-04-25 |
| M4 | Optional | Optional |

## Definition of Done (DoD)
A milestone is “done” when:
- [ ] Repro steps exist (commands, versions, data pointers)
- [ ] Metrics are reported + comparable to baseline
- [ ] Artifacts are committed (code/docs) and discoverable
- [ ] A demo (or evaluation script) exists
- [ ] Open issues are filed for follow-up work
