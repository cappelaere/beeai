# Contributing

This repository follows the workflow in **[OPERATING.MD](OPERATING.MD)**. Read it before opening a PR.

## GitHub issue first

- Define work in a **GitHub Issue** with clear **acceptance criteria** before implementation.
- Branch names: `feature/<issue-number>-short-name`, `fix/<issue-number>-short-name`, or `chore/<issue-number>-short-name` (see OPERATING.MD §9).
- The PR should **link the issue** (e.g. `Fixes #123` in the description).

## Plan → implement → review

1. **Plan** — Agree on an implementation plan (scope, files, tests, risks) before coding; do not expand beyond the issue.
2. **Implement** — Small, focused changes; follow existing patterns; add or update tests for behavior changes.
3. **Review** — PR is the review boundary; address feedback before merge.

## Commits

Use structured prefixes when possible (OPERATING.MD §10):

- `feat:` — new functionality  
- `fix:` — bug fix  
- `test:` — tests only  
- `chore:` — tooling, docs, non-functional  

## Validation

Run tests and checks relevant to your change. Example for Django/agent work:

```bash
cd agent_ui && ../venv/bin/python manage.py test <target_tests> -q
```

## PR description

Opening a PR pre-fills **[.github/pull_request_template.md](.github/pull_request_template.md)** — complete all sections.
