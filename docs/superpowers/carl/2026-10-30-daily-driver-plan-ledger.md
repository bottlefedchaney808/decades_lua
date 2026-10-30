# CARL ledger — WoW4_SiMs daily-driver plan — 2026-10-30

```yaml
mode: SPEC
subject: docs/superpowers/plans/2026-10-30-wow4-sims-daily-driver.md (+ paired spec)
author_family: qwen (strata local) — reviewers are different families (user-directed)
artifact_identity:
  plan: sha256:63fc38d6d7b63e4cc9762c90a1f836c3bc838d7ef0162803dd7a664eea9fb7d5
  spec: sha256:4348079d406646423abf36f8af0a34bbf7bbef958ac1279a626b8f3376fe2969
scope:
  in: [plan correctness, ordering, dependencies, verification quality, scrape failure modes, fallbacks]
  out: [locked decisions, wording, parent-vs-origin history reconciliation]
locked_decisions:
  - personal LAN daily driver, no hosting
  - stock UI + brand/theme pass only
  - tree-16 rescrape mandatory; Zephras+talents stretch
  - Tree A canonical, Tree B read-only reference, nothing deleted
  - ship Fri 2026-11-06, verify.sh + browser checklist = done
acceptance_gates:
  - verify.sh 11 PASS
  - browser checklist green on final build
reviewer_plan:
  r1: claude-code CLI 2.1.314 (Anthropic family) — dispatched first
  r2_r3: grok CLI 1.0.62 (xAI family) — packet written only after R1 returns + dispositions
  r4: not planned unless convergence fails
```

## Findings

| ID | Round | Severity | Finding | Evidence | Disposition | Resolution |
|---|---:|---|---|---|---|---|
| (pending R1) | | | | | | |

## Round log

- 2026-10-30 preflight done; R1 packet at `docs/superpowers/carl/r1-packet-claude.md`.
