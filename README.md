# <Project Name>

One-liner: what this project builds and why it matters.

## Quick Links
- Project Charter: [PROJECT_CHARTER.md](PROJECT_CHARTER.md)
- Roadmap: [ROADMAP.md](ROADMAP.md)
- How to contribute: [CONTRIBUTING.md](CONTRIBUTING.md)
- Decisions log: [DECISIONS.md](DECISIONS.md)

## Workflow (non-negotiables)
1. Work starts as an Issue.
2. Issues are assigned to an owner.
3. Work happens on a branch per issue.
4. PR must link the issue (`Fixes #123`).
5. PR must pass CI + review before merge.

## Repo Structure
- `docs/meetings/` meeting notes
- `docs/experiments/` experiment tracking + results
- `docs/datasets/` dataset cards + collection notes
- `docs/hardware/` hardware specs + BOM
- `docs/REFERENCE/` reference documents (see `docs/REFERENCE/README.md`)
- `src/` implementation (create as needed)
- `scripts/` utilities (create as needed)

## How to Run
> Fill these in once you have the first runnable artifact.

### Setup
```bash
# e.g. python -m venv .venv && source .venv/bin/activate
```

### Run
```bash
# e.g. python -m src.main --help
```

### Tests
```bash
# e.g. pytest
```

### License
Decise early. MIT/Apache-2.0 are common defaults.
---
