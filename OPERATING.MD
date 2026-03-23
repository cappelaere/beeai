# OPERATING.md

## Agentic Development Workflow (Codex + Cursor + GitHub)

---

# 1. Purpose

This document defines the **standard operating procedure** for implementing features and fixes using:

* **Codex** → Planning + Review Agent
* **Cursor** → Implementation Agent
* **GitHub** → System of record (issues, code, PRs)

Goal:

> Deliver small, correct, testable changes with a clear plan → implementation → review loop.

---

# 2. Core Principles

1. **Plan before code**
2. **Small, reviewable changes**
3. **Strict scope control**
4. **Test everything that changes**
5. **GitHub is the source of truth**
6. **Agents have clearly separated responsibilities**

---

# 3. Roles & Responsibilities

## Codex (Planning + Review Agent)

Responsibilities:

* Analyze repository structure
* Produce implementation plans
* Identify risks and dependencies
* Review completed work
* Validate against acceptance criteria

Must NOT:

* Implement code before plan approval
* Expand scope beyond issue

---

## Cursor (Implementation Agent)

Responsibilities:

* Execute approved plans
* Follow repo conventions
* Write minimal, correct code
* Add/update tests
* Run validation (lint, tests, type checks)

Must NOT:

* Change architecture without explicit instruction
* Modify unrelated files
* Expand scope

---

## GitHub (Control Plane)

Used for:

* Issues (task definition)
* Branches (work isolation)
* Pull Requests (review boundary)
* History (audit trail)

---

# 4. Workflow

## Phase 1 — Plan

1. Create GitHub Issue

2. Ask Codex:

   “Analyze repo and produce implementation plan. Do not code.”

3. Review and refine plan

4. Confirm acceptance criteria

---

## Phase 2 — Implement

1. Create branch:
   feature/<issue-number>-short-name

2. Give Cursor:

   * GitHub Issue
   * Approved plan

3. Cursor:

   * Implements step-by-step
   * Keeps changes minimal
   * Adds tests
   * Runs validation

---

## Phase 3 — Review

1. Open Pull Request

2. Provide Codex:

   * Issue
   * Plan
   * Diff / PR summary

3. Codex returns:

   * APPROVE / REQUEST CHANGES
   * Issues and gaps
   * Missing tests
   * Risks

4. Apply fixes if needed

5. Merge

---

# 5. Planning Standard (Codex Output)

Every plan MUST include:

1. Objective
2. Current State
3. Proposed Approach
4. Files Likely to Change
5. Step-by-Step Plan
6. Test Plan
7. Risks & Unknowns
8. Acceptance Criteria
9. Out of Scope

---

# 6. Implementation Rules (Cursor)

* Follow existing patterns
* Prefer smallest viable change
* Keep commits clean and focused
* Add/update tests for all changes
* Do not refactor unrelated code
* Stop and report if ambiguity is found

---

# 7. Required Implementation Output

Cursor must return:

1. Summary
2. Files Changed
3. Validation Performed
4. Remaining Risks
5. Suggested Commit Message

---

# 8. Review Standard (Codex)

Codex evaluates:

* Acceptance criteria compliance
* Correctness
* Regression risk
* Code quality
* Security issues
* Test completeness

Output must include:

* Verdict (APPROVE / REQUEST CHANGES)
* Criteria check
* Issues found
* Missing validation
* Recommended next step

---

# 9. Branch Naming Convention

feature/<issue>-<short-name>
fix/<issue>-<short-name>
chore/<issue>-<short-name>

Examples:

* feature/142-supervisor-claim
* fix/219-map-latlon-nan

---

# 10. Commit Message Standard

Use structured commits:

* feat: new functionality
* fix: bug fix
* test: tests added/updated
* chore: non-functional changes

Example:
feat: add supervisor claim workflow

---

# 11. Pull Request Template

## What changed

Summary of implementation

## Why

Link to issue and objective

## Files changed

* path/to/file — reason

## Validation

* Tests:
* Lint/type-check:
* Manual verification:

## Acceptance Criteria

* [ ] Criterion 1
* [ ] Criterion 2

## Risks / Follow-ups

List remaining concerns

---

# 12. Definition of Done

A task is complete when:

* Code implemented
* Tests pass
* Acceptance criteria satisfied
* PR reviewed and approved
* No critical risks remain

---

# 13. Anti-Patterns (Avoid)

* Coding without a plan
* Large, multi-purpose PRs
* Hidden scope expansion
* Skipping tests
* Ignoring repo conventions
* Mixing refactor + feature work

---

# 14. Future Enhancements (Optional)

* GitHub Actions for automated Codex review
* Auto-generated PR summaries
* Test coverage enforcement
* Agent-to-agent feedback loops

---

# 15. Guiding Principle

> “Plan small → Build small → Verify thoroughly → Iterate fast”

---
