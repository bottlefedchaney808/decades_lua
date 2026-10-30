# CARL ledger — WoW4_SiMs daily-driver plan — 2026-10-30

```yaml
mode: SPEC
subject: docs/superpowers/plans/2026-10-30-wow4-sims-daily-driver.md (+ paired spec)
artifact_identity_current:
  plan: (see git 2568f20; recompute sha256 before each round)
reviewer_plan:
  r1: claude-code CLI 2.1.314 — NEEDS_REVISION, 12 findings, all verified, patched in b813da8
  r2: grok CLI 1.0.62 — NEEDS_REVISION, 8 findings, all verified, patched in 2568f20
  r3: grok CLI — convergence check (pending)
```

## R1 dispositions (Claude Code) — all verified against files before patching

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| R1-F1 | crit | serve root must be dist/ with /forever/ base | AGREE → PATCHED |
| R1-F2 | crit | CLI is `sim --infile`, errors inside JSON | AGREE → PATCHED (later refined by R2-F2) |
| R1-F3 | crit | serve_tiles.py binds 127.0.0.1 by default | AGREE → PATCHED |
| R1-F4 | maj | node toggle loop is binary; new cats land in Mining | AGREE → PATCHED |
| R1-F5 | maj | audit.py has no count floors; needs dedupe | AGREE → PATCHED (later refined by R2-F5) |
| R1-F6 | maj | brand file list wrong (index.html, .tsx, .syso, gtag) | AGREE → PATCHED |
| R1-F7 | min | touch template before rebuild | AGREE → PATCHED |
| R1-F8 | min | automate page-200 checks | PARTIAL → browser stays manual; HTTP loop added in R2-F4 |
| R1-F9 | min | test counts 3/45 + separator golden test | AGREE → PATCHED |
| R1-F10 | min | scrape decision gate + places mapping | AGREE → PATCHED; reordering rejected, day-1 probe added in R2-F6 |
| R1-F11 | min | node 22 / package-lock assertion | LEFT — tsc-fail STOP is sufficient (R2 concurred) |
| R1-F12 | min | MAP remote exists; record both gitlinks | AGREE → PATCHED |

## R2 dispositions (Grok) — all verified against files before patching

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| R2-F1 | crit | verify.sh exit polarity inverted (ok=1/exit $ok) | AGREE → PATCHED |
| R2-F2 | crit | `not r.get('error')` fails on healthy sim (EmitUnpopulated) | AGREE → PATCHED, assert on error.message |
| R2-F3 | maj | routes/voyages never scripted or audited; no write_voyages | AGREE → PATCHED |
| R2-F4 | maj | spec-page HTTP 200 absent from verify.sh | AGREE → PATCHED (loop over 22 pages) |
| R2-F5 | maj | clamp to [0,1] still fails audit (half-open bound) | AGREE → PATCHED, reject with half-open rule |
| R2-F6 | min | day-2 gate races the sim build | AGREE → PATCHED, day-1 probe step |
| R2-F7 | min | brand middot dropped in makefile sed | AGREE → PATCHED |
| R2-F8 | min | launch.sh returns before ports listen | AGREE → PATCHED, wait loop |

R2 explicitly concurred with the F11 disposition and with keeping the browser checklist manual.
