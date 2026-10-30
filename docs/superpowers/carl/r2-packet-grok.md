You are CARL Round 2, an adversarial SPEC reviewer from a different model family than Round 1. Your job is to find what Round 1 missed and to challenge the driver's dispositions — not to re-derive Round 1's findings. Disagreement is useful; politeness is not the goal. If the artifact is now largely correct, say so instead of inventing issues.

## Artifacts under review (read fully)

1. `/home/zinko83/WoW4_SiMs/docs/superpowers/plans/2026-10-30-wow4-sims-daily-driver.md` — the implementation plan (PRIMARY, revised after R1)
2. `/home/zinko83/WoW4_SiMs/docs/superpowers/specs/2026-10-30-wow4-sims-daily-driver-design.md` — its design spec

**Artifact identity — quote this back verbatim:**
```
plan: sha256 c70878f09ff3858d193befddb9559b6a5e0624eced7742787d935af6500242b3
spec: sha256 d934c9cac89de03205e06dd8c259101380dafae7640b5acdc14d545fd0465e6b
```
Verify with `sha256sum`. If either hash differs, verdict MUST be INFRA_BLOCKED and you stop.

## Round 1 (Claude Code CLI, Anthropic family) — findings and dispositions

R1 verdict was NEEDS_REVISION with 12 findings. The driver verified each against the files and applied all of them (commit b813da8). Summary of what changed:

- R1-F1 critical AGREE/PATCHED: vite builds with `base: '/forever/'`; server now rooted at `dist/` with `/` redirect; all curls, verify.sh checks, and URLs use `/forever/`.
- R1-F2 critical AGREE/PATCHED: CLI is `wowsimcli sim --infile … --outfile …`; assertion now checks the JSON (`error` absent, `raidMetrics.dps.avg > 0`) because sim errors return inside the JSON.
- R1-F3 critical AGREE/PATCHED: `serve_tiles.py` launched with `--host 0.0.0.0 --port 8731`.
- R1-F4 major AGREE/PATCHED: node toggle loop is binary (herb vs everything-else); plan now specifies a prefix category map, new list divs, per-category hues.
- R1-F5 major AGREE/PATCHED: `audit.py` has no count floors; plan now requires adapter-side dedupe of `(n,ll)` and coordinate clamping; count guard lives in `write_datasets.BASELINE`.
- R1-F6 major AGREE/PATCHED: brand file list corrected (`ui/index.html` homepage, `social_links.tsx`, gtag strip, favicon excludes `*.syso`).
- R1-F7 minor AGREE/PATCHED: `touch ui/index_template.html` before rebuild; grep assertion on generated titles.
- R1-F8 minor PARTIAL: page-count nit acknowledged in passing; checklist-generation automation not adopted (browser checklist stays manual by design).
- R1-F9 minor AGREE/PATCHED: test counts 3/45; compact-separator rule for `places.js`; golden byte-equality test added.
- R1-F10 minor AGREE/PATCHED: scrape decision gate made explicit (day-2 cutoff, ship September data unchanged, skip Tasks 8–10, never mix generations); places→zones/landmarks mapping required in ENDPOINTS.md. NOT adopted: reordering Task 7 before the sim build — the sim build is the bigger unknown (never browser-verified) and the scrape gate is now time-bounded.
- R1-F11 minor LEFT: node 22 risk unproven; plan's "note deprecations, stop on tsc failure" stands. `package-lock.json` unchanged check not added.
- R1-F12 minor AGREE/PATCHED: MAP remote exists; Task 12 pushes MAP and records both gitlinks.

## Your job

1. Read the revised plan and spec. Attack what is still wrong, overstated, missing, unsafe, or untestable. The R1 fixes may have introduced new defects — check them.
2. Specifically pressure-test these driver dispositions you might disagree with:
   - F8 left manual (no automated page-200 loop in verify.sh).
   - F10 not reordered (scrape stays after the sim build, gated at day 2).
   - F11 left as-is (no `package-lock.json` unchanged assertion).
3. Do not relitigate the locked decisions: LAN-only personal daily driver, stock UI + brand/theme only, tree-16 rescrape mandatory with September-data fallback, Tree A canonical, ship Fri 2026-11-06.

## Context

`SIM=/home/zinko83/WoW4_SiMs/.publish/wow4_sims/upstream-classic`, `MAP=/home/zinko83/WoW4_SiMs/wow-forever`, `ROOT=/home/zinko83/WoW4_SiMs`. Go 1.23.4 at `/home/zinko83/tools/go/bin/go`, tests via `/usr/bin/python3 -m pytest`, node v22.22.1. Full background in `/home/zinko83/WoW4_SiMs/AUDIT-2026-10-30.md`. R1's full output is at `/tmp/carl_r1_claude.txt`.

## Required response format

Artifact-identity quote-back, then access proof (sha256sum output + one short quote from the revised plan proving you read the new version, not the old).

```
VERDICT: SHIP | SHIP_WITH_CAVEATS | NEEDS_REVISION | BLOCK | INFRA_BLOCKED
```

Findings:

```
### R2-F<n> — <severity: critical|major|minor>
- Claim: ...
- Evidence: <file:line or command output>
- Consequence: ...
- Replacement: <concrete text or step>
- Confidence: high|medium|low
```

Only findings with evidence. If the revised plan is largely correct, say so.
