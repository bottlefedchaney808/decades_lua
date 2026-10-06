# How to extend this knowledgebase

Rules for the next pass (beta logs, datamine, class videos, patch notes).

## One topic, one file

Do not dump a patch recap into overview. Put it in the matching file, then bump that file's "Last verified" line.

Class talent numbers go in `classes/<class>.md`. Itemization rules go in `systems/combat-itemization.md`. Spell IDs, when known, also go into `data/forever.yaml`.

## Confidence

Every new bullet gets a tag: `official` / `wowhead` / `press` / `classic-baseline` / `conflict` / `unknown`.

If a later source contradicts an earlier one, do not silently overwrite. Move the old claim into STATUS.md under Conflicts, keep both citations.

## Citations

Use the grounded-citations ledger (`sources.py`). Inline `[n]` only for ids already in the ledger. After adding a URL:

```
python C:/Users/bottl/.hermes/skills/research/grounded-citations/scripts/sources.py add <url>
python C:/Users/bottl/.hermes/skills/research/grounded-citations/scripts/sources.py render --replace-in knowledgebase/sources.md
```

Do not hand-type the Sources block.

## YAML

`data/forever.yaml` is the sim-facing contract. If a number is not in YAML, the sim must treat it as missing — never as 1.12 default unless the field is explicitly tagged `classic-baseline`.

## Class file recipe

Copy `classes/_template.md`. Fill only what is sourced. Leave rotation, stat weights, and BiS as `unknown` until logs exist.

## Sim scaffold

When a spec is ready to implement, flip its row in `wowsims/forever-sim-scaffold.md` from `stub` → `alpha` and add the spec id to YAML `sims.specs`.
