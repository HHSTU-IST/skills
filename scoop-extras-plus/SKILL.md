---
name: scoop-extras-plus
description: >
  Generate, update and lint Scoop manifests in the extras-plus bucket
  (bucket/*.json): scaffold from recipes, bump version, rehash, lint 23 rules.
  Triggers: scoop manifest, generate/update/lint manifest, checkver, autoupdate,
  hash, version bump, Excavator, extras-plus, scoop-extras-plus.
agent_created: true
---

# Scoop Extras Plus Manifest Forge

**Skill type**: process (流程型) — a three-command workflow (generate / update /
lint) plus a rule engine; the hard constraints are preconditions, not the point.

Turn "upstream shipped something new" or "upstream shipped a new version" into a
single command. All three trigger commands -- **generate / update / lint** --
share the recipe catalog and the rule engine. Python standard library only, and
everything runs offline except `--checkver`, `--fetch-hash` and `--rehash`.

**Target**: `$env:Scoop/buckets/extras-plus`, the copy of this bucket Scoop has
installed. The path is read from the environment at run time and is never
expanded in this package, so the globally installed skill works on any machine
and from any cwd. `--repo <path>` overrides it.

Package layout:

- `scripts/sm_lib.py` shared layer: paths (including the `$env:Scoop` lookup),
  serialization, the 15 builders, checkver, rule engine, README table sync
- `scripts/scoop_manifest.py` the three-command CLI
- `scripts/sm_selftest.py` self-check: recipes <-> builders, bucket resolution,
  docs <-> code, repo round-trip, lint baseline
- `references/manifest-fields.md` manifest field reference (this repo's rules)
- `references/recipes.md` when each of the 16 recipes applies, and what it emits
- `references/lint-rules.md` the 23 rules and how to fix each one
- `references/coverage.md` the upstream survey behind the catalog, and the gaps
- `assets/recipes.jsonc` the single source of truth for recipes: plain JSON under
  a deliberately non-`.json` name -- see "1. Hard constraints"

Scripts derive the package root themselves, so **they run from any cwd**:

```bash
python scripts/scoop_manifest.py <command> [options]
python scripts/sm_selftest.py
```

Globally installed at
`$env:USERPROFILE/.workbuddy/skills/scoop-extras-plus`, a junction onto this
repo's `skills/scoop-extras-plus`, so the repo stays the single source of truth.
Every example below is relative to the package root.

## 1. Hard constraints

- **Output**: `$env:Scoop/buckets/extras-plus/bucket/<app>.json`, optionally plus
  a README summary row in the same repo. Never write to `bin/`, `scripts/` or
  `.github/` -- those belong to Scoop's official scripts and to this repo's CI.
- **Preserve existing order**: `update` only slots **new** fields into their
  canonical position; existing fields keep their place. A full reorder needs an
  explicit `--reorder`.
- **Self-check before writing**: the result goes through the rule engine first,
  and error-level findings block the write (`--force` overrides).
- **Never add a `.json` file to this package.** The bucket CI hands Scoop's
  manifest gate every changed path matching its `*.json` include pattern -- a
  `-like` match on the repo-relative path, anywhere in the tree, so the `-Path`
  argument narrows nothing -- and validates each against `schema.json`. A
  non-manifest `.json` here therefore turns CI red. The recipe catalog is data,
  not a manifest, hence `assets/recipes.jsonc`: `*.json` does not match
  `.jsonc`. Keep the content strict JSON, because the name dodges the gate
  rather than licensing comments (`json-parse` in skill-draft would reject
  those). The CI mechanism is in section 7.
- **README is controlled**: the header must be exactly the three columns
  `App / Auto-Update ? / Note`, and a missing section skips the sync with an
  explanation. Centering already matches this repo's 5 tables byte for byte, so
  inserting a row never disturbs the others.

## 2. The three trigger commands

| Command | Alias | Job | Main options |
| :--- | :--- | :--- | :--- |
| **generate** | `gen` | Build a manifest from a recipe and fill it in, optionally sync README | `--list-recipes`, `--from`, `--recipe`, `--fetch-hash`, `--hash-from-file`, `--section`, `--dry-run` |
| **update** | `upd` | Edit fields / bump version + rewrite URLs / recompute hashes / probe upstream | `--name`, `--all`, `--set`, `--unset`, `--version`, `--rehash`, `--checkver [--apply]` |
| **lint** | `check` | Run the 23 rules, repair formatting | `--name`, `--json`, `--strict`, `--fix-format`, `--rules` |

Shared option `--repo <bucket repo root>` overrides the target. Without it the
script takes `$env:Scoop/buckets/extras-plus` whenever that is a bucket repo, and
otherwise walks up from the cwd looking for a directory holding both `bucket/`
and `README.md`.

## 3. generate

**Settle five things first** and ask the user for anything missing; do not guess:

1. Who is upstream: a GitHub repo, or a website / own CDN?
2. What ships: portable archive / NSIS installer / InnoSetup / bare exe / plugin?
3. Version number (without the leading `v`)
4. Where the entry point is: the exe a shortcut should point at (relative to
   `$dir`, backslashes) and any command-line alias
5. README section: `AI Specific` / `General Use` / `Academic Tools` /
   `Development Tools` / `Win-Only`

Unsure about the recipe? Run `--list-recipes` first; it prints when each recipe
applies, the required and optional parameters, and same-kind samples (from this
repo where a manifest of that shape exists, from the upstream bucket otherwise).
Then compare against `references/recipes.md`.

```bash
python scripts/scoop_manifest.py gen --name myapp --recipe github-nsis-7z \
  --version 3.4.5 --desc "Super app for testing the generator" \
  --homepage https://github.com/o/r --license MIT \
  --url64 "https://github.com/o/r/releases/download/v3.4.5/app.exe#/dl.7z" \
  --repo-url https://github.com/o/r \
  --shortcut-exe app.exe --shortcut-name "MyApp" \
  --section "General Use" --dry-run

python scripts/scoop_manifest.py gen --from specs.json --section "General Use"
```

`--from` reads a spec file, which suits batches: an object or an array of
objects whose keys are the `param_docs` names from `recipes.jsonc`, plus
`name`, `recipe` and `section`. Command-line options win over the file.

**Pick one of three ways to obtain the hash, never invent it**: `--fetch-hash`
streams the download and computes it; `--hash-from-file <path>` uses a package
already on disk; if neither is given, run `bin/checkhashes.ps1` afterwards (the
command prints that hint).

**Rhythm**: `--dry-run` to preview, then drop it to write and sync the README,
then `lint --name <app>` to confirm.

## 4. update

`--set` takes a dotted path and parses the value as JSON, falling back to a
string. New fields land in their canonical key position (`persist` goes between
`extract_to` and `env_set`, not at the end of the file); `--unset` deletes.

```bash
python scripts/scoop_manifest.py upd --name myapp \
  --set 'description=Portable note taking app' --set 'persist=data' \
  --set 'shortcuts.0.1=MyApp Pro'

python scripts/scoop_manifest.py upd --name myapp --checkver   # report
python scripts/scoop_manifest.py upd --name myapp --checkver --apply --rehash
python scripts/scoop_manifest.py upd --name myapp --version 3.5.0  # manual
python scripts/scoop_manifest.py upd --all --checkver --apply --rehash  # sweep
```

`--version` rewrites the old version hard-coded in every download URL.

`--checkver` understands the `github` string, `{"github": ...}`, bare-string
regex (scraped from `homepage`), `{"url", "regex"}`, `{"url", "jsonpath",
"regex", "replace"}`, `{"url", "xpath", ...}` and `{"sourceforge": ...}`.
**The `{"script": ...}` form needs a Scoop environment and explicitly reports that
it cannot probe offline**; use `bin/checkver.ps1` instead.

Safety net: the rule engine runs after every change and error-level findings
**block the write** (`--force` overrides); `--dry-run` previews and
`--print-json` dumps the result. `upd` leaves the README alone unless `--readme`
is passed, which syncs it and keeps the existing note column (for example
`by @CronusLM`).

## 5. lint

```bash
python scripts/scoop_manifest.py lint                  # full run, about 1 second
python scripts/scoop_manifest.py lint --name aionui    # a single app
python scripts/scoop_manifest.py lint --json           # machine-readable report
python scripts/scoop_manifest.py lint --strict         # warnings fail too
python scripts/scoop_manifest.py lint --fix-format     # formatting only
python scripts/scoop_manifest.py lint --rules          # print the rule catalog
```

`--fix-format` touches formatting only (indent / CRLF / trailing newline) and
never JSON semantics.

Line endings are checked repo-wide, not just per manifest: a full `lint` also
walks the working tree -- skipping `.git/` and the tool caches -- and reports
every text file that is not CRLF, which is what `.editorconfig` demands for
`[*]`. That pass is read-only and reaches into directories this skill does not
own; `--fix-format` normalises only `bucket/*.json` and `README.md`. The traps
inside that pass are in section 7.

Exit code: error-level findings give 1; warnings alone give 0, or 1 with
`--strict`. Rules and their fixes live in `references/lint-rules.md`.

**Baseline**: 0 error-level findings anywhere in the bucket. `lint` prints the
live counts, because the bucket grows with every autoupdate commit. Real issues
found so far:

| manifest | Issue | Rule |
| :--- | :--- | :--- |
| `cumora` | `version` says 0.18.4 but the URL and autoupdate both pin `v0.1.64` with no `$version`, so it installs an old build forever | W104 + W110 |
| `voov-meeting` | `hash` written as `md5:03fd...`, a prefix Scoop does not accept | E011 |
| 7 manifests | `architecture` exists but `autoupdate` has only a flat url, so Excavator never refreshes the per-architecture URLs | W103 |
| `aionui` / `ecopaste` | the README summary table spells them `aionaui` / `ecopast` | W105 |
| `affinity` | `description` ends with a period (Scoop wants a phrase) | W101 |

Line endings are no longer among them: `isobuster` used to be the one file
written with LF, and it has since been normalised. W112 watches that class of
problem across the whole working tree, instead of leaving it to a per-manifest
rule.

## 6. Boundaries

Not for: installers that need interaction, MSI customisation, or packages with
private unpacking logic beyond `$PLUGINSDIR` (hand-writing is easier); archives
over 2GB (aria2 and hash verification degrade); **32bit architecture** — `arch`
takes `64bit` and `arm64` only, so `url32` / `hash32` are neither accepted nor
emitted; and any change under `bin/`, `scripts/` or `.github/`.

## 7. Gotchas

One entry per thing the bucket, its CI or the tooling has surprised us with. Add
a line as soon as a new one shows up -- this is where the density is.

- **A non-manifest `.json` anywhere in this package turns CI red.**
  Symptom: CI fails on a file that is plainly not a manifest.
  Cause: the bucket CI hands Scoop's manifest gate every changed path matching
  its `*.json` include pattern -- a `-like` match on the repo-relative path,
  anywhere in the tree, so the `-Path` argument narrows nothing -- and validates
  each against `schema.json`.
  Action: keep data in `assets/recipes.jsonc` (or a `.py` module). The suffix is
  the whole point -- `*.json` does not match `.jsonc` -- and the content stays
  strict JSON, since the rename dodges the gate rather than licensing comments
  (`json-parse` in skill-draft would reject those).
- **The installed bucket outranks the cwd.**
  Symptom: run the script from inside a different checkout of this bucket, pass
  no `--repo`, and the manifest lands in the installed copy.
  Cause: the resolution order is `--repo`, then the installed copy under
  `$env:Scoop/buckets/extras-plus`, then a walk up from the cwd -- this build
  deliberately prefers the copy Scoop has installed.
  Action: pass `--repo <path>` whenever you mean the checkout you are standing
  in.
- **The line-ending pass reaches outside this skill, and it is read-only.**
  Symptom: `lint` reports files under `bin/`, `scripts/` and `.github/`.
  Cause: `W112` walks the whole working tree, because `.editorconfig` demands
  CRLF for `[*]`; those directories belong to Scoop and to the repo's CI.
  Action: leave them alone. `--fix-format` normalises only the two things this
  skill owns, `bucket/*.json` and `README.md`, and a README sync writes CRLF
  unconditionally, so it cannot quietly strip the endings from a file it only
  meant to add one row to.
- **README recognition is exact, and an unknown table is skipped.**
  Symptom: a summary row never appears, and nothing is reported as wrong.
  Cause: the header must be exactly the three columns
  `App / Auto-Update ? / Note`; anything else is left untouched rather than
  guessed at, and a missing section skips the sync with an explanation.
  Action: match the existing header -- centering already matches this repo's 5
  tables byte for byte, so an inserted row never disturbs the others.
- **A `{"script": ...}` checkver cannot be probed offline.**
  Symptom: `--checkver` reports that it cannot probe the manifest.
  Cause: the script form needs a live Scoop environment, which the command does
  not have.
  Action: run `bin/checkver.ps1` instead.
- **The self-check measures the installed bucket, not this package.**
  Symptom: `sm_selftest.py` fails on a manifest you have never touched.
  Cause: the round-trip and lint-baseline groups read
  `$Scoop/buckets/extras-plus`, which grows with every autoupdate commit -- the
  package ships no bucket of its own.
  Action: read the failure as news about the bucket rather than a broken skill;
  the package groups (catalog, docs, name) are the ones judging the package.

## 8. Maintenance

```bash
python scripts/sm_selftest.py            # full self-check (offline)
python scripts/sm_selftest.py --verbose  # print every detail
```

The self-check has 7 groups, in run order: recipe catalog shape, recipe <->
builder coverage both ways and the no-`.json` guard -> bucket resolution
(`$env:Scoop/buckets/extras-plus` is the default target, `--repo` overrides it,
and no hard-coded Scoop root appears anywhere in the package) -> virtual
rendering of all 16 recipes -> repo serialization round-trip -> README table
round-trip and row-insert idempotence -> the lint baseline over the real bucket
-> docs <-> code consistency (`lint-rules.md` matches `RULES` word for word,
`recipes.md` maps one-to-one onto `recipes.jsonc`, and `SKILL.md`'s `name`
equals the directory name).

**Adding a recipe** (4 steps, and the self-check catches omissions): add an entry
to the `recipes` array in `recipes.jsonc` (`id` / `label` / `when` /
`builder` / `required` / `refs`) and document any new parameters in `param_docs`
-> register
a builder of the same name in `BUILDERS` in `sm_lib.py` -> add a `## <recipe id>`
section to `recipes.md` -> run `sm_selftest.py`.

**Adding a rule**: change `RULES` in `sm_lib.py` and the table in
`lint-rules.md` together, keeping the wording identical.

**Editing docs**: all four markdown files pass `rumdl check` at its default
(width <= 80 columns); finish with `rumdl fmt`.
