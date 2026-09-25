---
name: scoop-main-plus
description: >
  Generate, update and lint Scoop manifests in the main-plus bucket
  (bucket/*.json): scaffold from recipes, bump version, rehash, lint 25 rules.
  Triggers: scoop manifest, generate/update/lint manifest, checkver, autoupdate,
  hash, version bump, Excavator, main-plus, scoop-main-plus.
agent_created: true
---

# Scoop Main-Plus Manifest Forge

**Skill type**: process (流程型) — a three-command workflow (generate / update /
lint) plus a rule engine; the hard constraints are preconditions, not the point.

Turn "upstream shipped something new" or "upstream shipped a new version" into a
single command. All three trigger commands -- **generate / update / lint** --
share the recipe catalog and the rule engine. Python standard library only, and
everything runs offline except `--checkver`, `--fetch-hash` and `--rehash`.

Package layout:

- `scripts/sm_lib.py` shared layer: paths, serialization, the 18 builders,
  checkver, rule engine, README table sync
- `scripts/scoop_manifest.py` the three-command CLI
- `scripts/sm_selftest.py` self-check: recipes <-> builders, docs <-> code,
  repo round-trip, lint baseline
- `references/manifest-fields.md` manifest field reference (this repo's rules)
- `references/recipes.md` when each of the 18 recipes applies, and what it emits
- `references/lint-rules.md` the 25 rules and how to fix each one
- `references/coverage.md` the upstream survey behind the catalog, and the gaps
- `assets/recipes.jsonc` the single source of truth for recipes. The `.jsonc`
  suffix is deliberate -- see the hard constraints below

Scripts derive the package root themselves, so **they run from any cwd**. The
target bucket is resolved on every run, in this order:

1. `--repo <path>`, when given;
2. the cwd, walked upwards -- running inside any bucket edits that bucket;
3. **`$Scoop/buckets/main-plus`** -- the global fallback, which is what lets an
   installed copy write into this bucket from anywhere else.

`$Scoop` is read from the environment (`SCOOP`, then `Scoop`). The expanded path
is **never** stored in the skill -- the same package has to work on any machine.

```bash
python scripts/scoop_manifest.py <command> [options]
python scripts/sm_selftest.py
```

Pure standard library, and the repo's Python target is 3.14; nothing in the
scripts is version-gated, so an older 3.x still runs them.

## Hard constraints

- **Output**: `<repo>/bucket/<app>.json`, optionally plus a README summary row.
  Never write to `bin/`, `scripts/` or `.github/` -- those belong to Scoop's
  official scripts and to this repo's CI.
- **Never bake `$Scoop` in.** No file may hold the resolved path
  (`<drive>:\...\buckets\...`); the environment is read on every run, so one
  package works on every machine. The self-check fails if a literal reappears.
- **Never add a `.json` data file inside this skill.** A non-manifest `.json`
  here turns CI red, which is why the catalog is `assets/recipes.jsonc`; use
  `.jsonc` (or a `.py` module) for any further data. The CI mechanism it dodges
  is in section 7.
- **Preserve existing order**: `update` only slots **new** fields into their
  canonical position; existing fields keep their place. A full reorder needs an
  explicit `--reorder`.
- **Self-check before writing**: the result goes through the rule engine first,
  and error-level findings block the write (`--force` overrides).
- **This bucket is bin-first**: it installs 39 of its 40 packages through `bin`
  and declares no `shortcuts` at all. Reach for a shortcut only when the package
  really is a desktop app -- section 7 explains what happens when you do.
- **README is controlled**: the table lives under `## ⭐️ Summary` with the three
  columns `App / Language / Auto-Update ?`. A missing section skips the sync with
  an explanation, and a column the skill does not recognise is never touched.

## The three trigger commands

| Command | Alias | Job | Main options |
| :--- | :--- | :--- | :--- |
| **generate** | `gen` | Build a manifest from a recipe and fill it in, optionally sync README | `--list-recipes`, `--from`, `--recipe`, `--fetch-hash`, `--hash-from-file`, `--language`, `--flat-url`, `--dry-run` |
| **update** | `upd` | Edit fields / bump version + rewrite URLs / recompute hashes / probe upstream | `--name`, `--all`, `--set`, `--unset`, `--version`, `--rehash`, `--readme`, `--checkver [--apply]` |
| **lint** | `check` | Run the 25 rules, repair formatting | `--name`, `--json`, `--strict`, `--fix-format`, `--rules` |

Shared option `--repo <bucket repo root>`. Without it the script walks up from
the cwd looking for a directory holding both `bucket/` and `README.md`, and
falls back to `$Scoop/buckets/main-plus` when there is none -- so a copy that is
installed elsewhere still writes into this bucket.

## generate

**Settle six things first** and ask the user for anything missing; do not guess:

1. Who is upstream: a GitHub repo, or a website / own CDN?
2. What ships: portable archive / NSIS installer / InnoSetup / bare exe / a
   vendor toolchain that is never shimmed?
3. Version number (without the leading `v`)
4. What goes on PATH: the exe `bin` should point at (relative to `$dir`), and any
   command-line alias. Most packages in this bucket need nothing else.
5. Whether a Start-menu shortcut is genuinely wanted. If it is, the package is
   not a CLI tool and `github-cli-archive` is the wrong recipe.
6. README: the implementation language (Rust / Go / Python / C++ / ...)

Unsure about the recipe? Run `--list-recipes` first; it prints when each recipe
applies, the required and optional parameters, and same-kind samples (from this
repo where a manifest of that shape exists, from the upstream main bucket
otherwise). Then compare against `references/recipes.md`.

```bash
python scripts/scoop_manifest.py gen --name mytool --recipe github-cli-archive \
  --version 3.4.5 --desc "Super fast text transformer" \
  --homepage https://github.com/o/r --license MIT \
  --url64 "https://github.com/o/r/releases/download/v3.4.5/tool-x86_64-pc-windows-msvc.zip" \
  --repo-url https://github.com/o/r \
  --bin-exe tool.exe --language Rust --dry-run

python scripts/scoop_manifest.py gen --from specs.json --language Go
```

`--from` reads a spec file, which suits batches: an object or an array of
objects whose keys are the `param_docs` names from `recipes.jsonc`, plus `name`,
`recipe` and `language`. Command-line options win over the file.

**Architecture**: `--arch 64bit+arm64` emits an `architecture` block with
`url64` / `url_arm64`. A single architecture still gets a block for the recipes
that set `arch_block` (`github-cli-archive`, `toolchain-env`,
`github-single-exe`), because that is what 20 of the 40 manifests here do; pass
`--flat-url` to collapse it to a top-level `url` / `hash` instead.

**32bit is not supported.** This bucket ships 64bit and arm64 only: `arch`
accepts just those two, and there is no `--url32` / `--hash32`. What upstream
still carries is survey data, not an option -- see section 7.

**Pick one of three ways to obtain the hash, never invent it**: `--fetch-hash`
streams the download and computes it; `--hash-from-file <path>` uses a package
already on disk; if neither is given, run `bin/checkhashes.ps1` afterwards (the
command prints that hint).

**Rhythm**: `--dry-run` to preview, then drop it to write and sync the README,
then `lint --name <app>` to confirm.

## update

`--set` takes a dotted path and parses the value as JSON, falling back to a
string. New fields land in their canonical key position (`persist` goes between
`extract_dir` and `env_set`, not at the end of the file); `--unset` deletes.

```bash
python scripts/scoop_manifest.py upd --name mytool \
  --set 'description=Fast text transformer' --set 'persist=data' \
  --set 'bin.0.1=tt'

python scripts/scoop_manifest.py upd --name mytool --checkver   # report
python scripts/scoop_manifest.py upd --name mytool --checkver --apply --rehash
python scripts/scoop_manifest.py upd --name mytool --version 3.5.0  # manual
python scripts/scoop_manifest.py upd --all --checkver --apply --rehash  # sweep
```

`--version` rewrites the old version hard-coded in every download URL.

`--checkver` understands the `github` string, `{"github": ...}`, bare-string
regex (scraped from `homepage`), `{"url", "regex"}`, `{"url", "jsonpath",
"regex", "replace"}`, `{"url", "xpath", ...}` and `{"sourceforge": ...}`.
`"reverse": true` is honoured, so a manifest whose candidates run newest-last
reports the **last** match instead of the first.
**The `{"script": ...}` form cannot be probed offline**; use `bin/checkver.ps1`
instead (section 7).

Safety net: the rule engine runs after every change and error-level findings
**block the write** (`--force` overrides); `--dry-run` previews and
`--print-json` dumps the result. `upd` leaves the README alone unless `--readme`
is passed, which syncs the row and keeps every cell it does not own.

## lint

```bash
python scripts/scoop_manifest.py lint                  # full run, about a second
python scripts/scoop_manifest.py lint --name choose    # a single app
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

**Baseline (40 manifests)**: 0 errors, 11 warnings, 29 fully clean. Real issues
found so far:

| manifest | Issue | Rule |
| :--- | :--- | :--- |
| `calepin`, `docker-completion`, `muscle`, `seqkit`, `vsearch` | missing from the README summary table | W105 |
| `commix` | `license` is a URL, not an SPDX identifier | W106 |
| `qlty`, `rheo`, `shiroa` | `license` is prose (`Business Source License 1.1`, `Apache-2.0 license`) | W106 |
| `micromamba`, `n-m3u8dl-re`, `typst-ts` | `version` carries non-numeric parts (`2.9.0-0`, `0.6.0-beta`, `0.8.0-rc3`), which autoupdate can mishandle | W107 |

Line endings are no longer among them: `typst-ts` was the only file written with
LF, and it has since been normalised. `W112` watches that class of problem
across the whole working tree instead of leaving it to a per-manifest rule.

## Boundaries

Not for: installers that need interaction, MSI customisation, or packages with
private unpacking logic beyond `$PLUGINSDIR` (hand-writing is easier); archives
over 2GB (aria2 and hash verification degrade); `.jar` launchers, which need a
hand-written `.cmd` shim; and any change under `bin/`, `scripts/` or `.github/`.

## Gotchas

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
- **A resolved `$Scoop` path anywhere fails the self-check.**
  Symptom: `sm_selftest.py` reports a literal `<drive>:\...\buckets\...`.
  Cause: the environment is read on every run precisely so that one package
  works on every machine; a stored copy breaks that promise.
  Action: read `SCOOP`, then `Scoop`, at run time; never bake the result in.
- **`arch 32bit` is refused on purpose, and upstream still carries it.**
  Symptom: passing `32bit` fails with a deliberate message rather than a generic
  typo complaint.
  Cause: this bucket ships 64bit and arm64 only, so there is no `--url32` /
  `--hash32` to accept it.
  Action: use `64bit+arm64`. The 528 upstream files that still declare `32bit`
  are survey data in `references/coverage.md`, not a supported option.
- **A `{"script": ...}` checkver cannot be probed offline.**
  Symptom: `--checkver` reports that it cannot probe the manifest.
  Cause: the script form needs a live Scoop environment, which the command does
  not have.
  Action: run `bin/checkver.ps1` instead.
- **`"checkver": "github"` reads `homepage`, never the download URL.**
  Symptom: `ERROR <app> checkver expects the homepage to be a github
  repository`, then a 404 against `<homepage>/releases/latest`.
  Cause: the string form takes the repo from `homepage` alone, so a project
  whose homepage is a Pages site or its own domain breaks it -- `moviebox` and
  `music-dl` both did, while `lint` stayed green because this skill's probe
  falls back to the repository in the download URL.
  Action: use `{"github": "https://github.com/o/r"}` and leave `homepage`
  pointing at the real site.
- **A `checkver` that scrapes an HTML page can go quiet.**
  Symptom: `couldn't match '<regex>' in <url>` -- no update, no 404, no clue.
  Cause: the page now renders its list client-side, so the version never
  reaches the HTML; `anaconda.org/conda-forge/micromamba/files` did this to
  `micromamba`.
  Action: find the JSON endpoint behind it. For anaconda that is
  `api.anaconda.org/release/<owner>/<package>/latest`, which lists only the
  newest release's distributions and is roughly 180x smaller than the full
  file listing.
- **The self-check measures the installed bucket, not this package.**
  Symptom: `sm_selftest.py` fails on a manifest you have never touched.
  Cause: the round-trip and lint-baseline groups read
  `$Scoop/buckets/main-plus`, which grows with every autoupdate commit -- the
  package ships no bucket of its own.
  Action: read the failure as news about the bucket rather than a broken skill;
  the package groups (catalog, docs, name) are the ones judging the package.
- **The line-ending pass reaches outside this skill, and it is read-only.**
  Symptom: `lint` reports files under `bin/`, `scripts/` and `.github/`.
  Cause: `W112` walks the whole working tree, because `.editorconfig` demands
  CRLF for `[*]`; those directories belong to Scoop and to the repo's CI.
  Action: leave them alone. `--fix-format` normalises only the two things this
  skill owns, `bucket/*.json` and `README.md`, and a README sync writes CRLF
  unconditionally, so it cannot quietly strip the endings from a file it only
  meant to add one row to.
- **`github-cli-archive` refuses a shortcut.**
  Symptom: a package that genuinely ships a desktop app cannot use the obvious
  recipe.
  Cause: this bucket is bin-first -- 39 of its 40 packages install through `bin`
  and it declares no `shortcuts` at all -- so the recipe declines one on
  purpose.
  Action: read the refusal as the signal that the package is not a CLI tool, and
  pick a recipe that emits `shortcuts`.
- **The rule engine has a blind spot: archive format versus `autoupdate`.**
  Symptom: `lint` is green, yet the installed build is the wrong one.
  Cause: no rule compares the install archive's extension with the URL
  `autoupdate` points at. `typst-ts` installs from a `.zip` while its
  `autoupdate` points at a `.tar.gz`.
  Action: check that pair by hand.
- **A release that renames its assets breaks `autoupdate`, and no rule sees it.**
  Symptom: Excavator reports `URL ... is not valid`, then
  `ERROR Could not update <app>, hash for <file> failed!`.
  Cause: the manifest's `autoupdate.url` still spells the old asset name, so
  the built URL 404s. `sttr` renamed `sttr_<version>_windows_amd64.zip` to
  `sttr_Windows_x86_64.zip` at 0.2.28 and the manifest sat at 0.2.24.
  Action: compare the URL against the release's asset list
  (`gh api repos/<o>/<r>/releases`), then rehash from the same release. Read
  the new name literally -- do not carry `$version` into the file name.
- **Upstreams that publish tag-only releases make `checkver: "github"` chase
  a version with no binaries.**
  Symptom: Excavator bumps the version, then `Could not update <app>`.
  Cause: `github` reads the newest release, whatever it contains; `shimmy`
  shipped v2.6.2-v2.6.4 with an empty asset list, so only v2.6.1 was
  installable.
  Action: point `checkver.url` at the releases API and match on an asset URL
  instead of the tag -- `/download/v([\d.]+)/<asset>\\.exe` picks the newest
  release that actually ships the file.

## Maintenance

```bash
python scripts/sm_selftest.py            # full self-check (offline)
python scripts/sm_selftest.py --verbose  # print every detail
```

The self-check has 7 groups, numbered in run order: recipe catalog shape and
architecture policy -> virtual rendering of all 18 recipes from their own
declared parameters -> skill package consistency (`lint-rules.md` matches
`RULES` word for word, `recipes.md` maps one-to-one onto `recipes.jsonc`,
`SKILL.md`'s `name` equals the directory name, and every `references/*.md` is
indexed by `SKILL.md`) -> path resolution policy (no
expanded `$Scoop` baked in, and `$Scoop/buckets/main-plus` really is the
fallback) -> repo serialization round-trip -> README table round-trip,
row-insert idempotence and the no-op re-sync -> the lint baseline over the real
bucket.

**Adding a recipe** (4 steps, and the self-check catches omissions): add an entry
to the `recipes` array in `recipes.jsonc` (`id` / `label` / `when` / `builder` /
`required` / `optional` / `refs`) and document any new parameters in
`param_docs` -> register a builder of the same name in `BUILDERS` in
`sm_lib.py` -> add a `## <recipe id>` section to `recipes.md` -> run
`sm_selftest.py`. Base a new recipe on a population recorded in
`references/coverage.md`, not on a single manifest, and update section 9 there
in the same pass.

**Adding a rule**: change `RULES` in `sm_lib.py` and the table in
`lint-rules.md` together, keeping the wording identical.

**Editing docs**: all four markdown files pass `rumdl check` at its default
(width <= 80 columns); finish with `rumdl fmt`.
