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
`by @CronusLM`); `--readme` only fires when something else in the manifest
changed (see section 7).

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
walks the working tree -- skipping `.git/` only, so `.rumdl_cache/` shows up
too -- and reports every text file that is not CRLF, which is what
`.editorconfig` demands for `[*]`. That pass is read-only and reaches into
directories this skill does not own; `--fix-format` normalises only
`bucket/*.json` and `README.md`. The traps inside that pass are in section 7.

Exit code: error-level findings give 1; warnings alone give 0, or 1 with
`--strict`. Rules and their fixes live in `references/lint-rules.md`.

**Baseline**: 0 error-level findings anywhere in the bucket. `lint` prints the
live counts, because the bucket grows with every autoupdate commit. Real issues
found so far:

| manifest | Issue | Rule |
| :--- | :--- | :--- |
| `cumora` | `version` says 0.18.7 but the URL and autoupdate both pin `v0.1.64` with no `$version`, so it installs an old build forever | W104 + W110 |
| `voov-meeting` | `hash` written as `md5:03fd...`, a prefix Scoop does not accept | E011 |
| 4 manifests | `architecture` exists but `autoupdate` has only a flat url, so Excavator never refreshes the per-architecture URLs: `bitcomet`, `comfyui-manager`, `hermes-one`, `mineru` | W103 |
| 8 manifests | no README summary row at all: `comfyui`, `comfyui-manager`, `cumora`, `dingtalk-en`, `dorion`, `genoffice`, `hermes-one`, `isobuster` | W105 |
| `affinity` | `description` ends with a period (Scoop wants a phrase) | W101 |

Fixed 2026-09-25 and gone from the list: the README spelled `aionui`,
`ecopaste` and `bananas` as `aionaui`, `ecopast` and `p2p-kiwi` (W105), and `wake`
had no row at all; `notegen`, `open-design` and `defender-remover` got real
hashes plus per-architecture `autoupdate` (their W103 is gone, 7 -> 4), and
`zlibrary` stopped scraping the dead `1lib.sk` page -- it now dates its version
from the CDN build it actually downloads.

Line endings are still among them, by one file: `isobuster` is written with LF
(0 CRLF against 23 LF, W109) and has not been normalised. W112 watches that class
of problem across the whole working tree, which is also where the `.rumdl_cache/`
files are reported -- those are the linter's own cache, not the bucket's.

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
- **A `{"script": ...}` checkver still downloads `checkver.url` first.**
  Symptom: the script is never reached -- Excavator reports the download error
  (`The SSL connection could not be established`, `URL <homepage> is not valid`)
  even though the script reads a completely different URL.
  Cause: `bin/checkver.ps1` fetches `checkver.url`, falling back to `homepage`
  under its "Not Specified" branch, and `continue`s on a transport error
  *before* `Invoke-Command` runs the script. A dead homepage therefore sinks a
  script checkver that never uses it (`zlibrary`, whose only reachable upstream
  host is the CDN).
  Action: add a `url` that answers 200 and is cheap -- the script overwrites
  `$page`, so the body is discarded (`https://s3proxy.cdn-zlib.sk/`, 615 bytes).
  Then probe it with `bin/checkver.ps1`: without that fetch step the script is a
  no-op and the symptom looks like a script bug.
- **A prefixed tag or a rolling `latest` release defeats the built-in regex.**
  Symptom: `couldn't match '/releases/tag/(?:v|V)?([\d.]+)' in
  https://api.github.com/repos/o/r/releases/latest`.
  Cause: the default `github` regex assumes the tag is `v<digits>`. Tags such as
  `open-design-v0.24.1` / `note-gen-v0.37.1` never match, and a `/releases/latest`
  that points at a rolling release (`vsnapshot`, `web-39e6ba2f`) never matches
  either -- even when the real versions sit right below it.
  Action: move the endpoint into `checkver.url` and either anchor on
  `"tag_name\"\\s*:\\s*\"<prefix>v([\\d.]+)\""`, or point at the releases *list*
  with `/releases/tag/v([\\d.]+)` -- `Match` takes the first hit in document
  order, so a rolling release is simply skipped (`watt-toolkit`, `linkandroid`).
- **A dash-suffixed version gets truncated, and the truncated URL 404s.**
  Symptom: the app is reported a version that does not exist, the download 404s,
  and Excavator fails with `Could not update <app>`.
  Cause: `jupyterlab-desktop` tags are `v4.6.3-1`; the built-in regex stops at
  the dash and yields `4.6.3`.
  Action: capture the suffix explicitly --
  `"regex": "tag_name\"\\s*:\\s*\"v?([\\d.]+(?:-\\d+)?)\""` -- and read the W107
  warning as a nudge to double-check the comparison, not as a blocker.
- **Upstream can retire the GitHub release assets, or move the repo.**
  Symptom: the API lists a release with an empty `assets` array, or the asset
  names change between versions; hash extraction finds nothing and the fallback
  download 404s.
  Cause: `aionui` moved its installers to `static.aionui.com/releases/$version/`
  and left a note in the release body; `mistweaverco/bananas` renamed itself to
  `dont-be-evil-company/p2p.kiwi` and renamed every asset
  (`bananas-setup_x64.exe` -> `p2p-kiwi-setup_x64.exe`, entry exe
  `bananas.exe` -> `p2p-kiwi.exe`); `debpalash/VoiceStudio` kept its repo, its
  `v` tag and its version scheme but repackaged Tauri -> electron-builder
  between 0.5.3 and 0.5.4, so its MSI (`VoiceStudio_0.5.3_x64_en-US.msi`, still
  published under v0.5.3) stops existing from v0.5.4 on.
  Action: read the release body first, then the project site's JS bundle -- the
  download template is usually a one-liner in it. Rewrite `url` + `autoupdate`,
  and fix `shortcuts` / `bin` when the entry exe was renamed too. Non-GitHub URLs
  get their hash by downloading, which is fine. When `checkver` is healthy and
  only the download 404s, diff the asset list of the last few releases to find
  the migration point instead of trusting the latest one: `voicestudio` 0.5.6
  needed `VoiceStudio-Electron-$version-win-x64.exe#/dl.7z` plus a `shortcuts`
  retarget, `PFiles\VoiceStudio\omnivoice-studio.exe` -> `VoiceStudio.exe`.
- **electron-builder leaves files outside `app-64.7z`, and `extract_dir` drops
  them.**
  Symptom: the app installs and launches, but a bundled sample the vendor
  installer would have placed is missing.
  Cause: the outer NSIS archive of `VoiceStudio` 0.5.6 carries
  `$PLUGINSDIR\app-64.7z`, the `$R0` uninstaller slot *and* plain
  `resources\backend\assets\samples\...`; the dominant
  `extract_dir: "$PLUGINSDIR"` idiom keeps only the first and discards the rest.
  Action: read `7z l` of the installer for top-level entries other than
  `$PLUGINSDIR` -- the inner payload holds only the sample metadata, not the
  clips. When such entries exist, drop `extract_dir` / `extract_to` and clean up
  from `post_install` instead, the shape `ecopaste` and `notegen` use, adding
  the `$R0` slot to the paths it removes.
- **`upd --readme` only fires when another field changed.**
  Symptom: `upd --name X --readme --section "General Use"` prints
  `nothing to change.` and the README keeps its old row.
  Cause: `_sync_readme` sits after the `if not changed: return 0` early exit.
  Action: pair it with a harmless `--set` -- re-setting the same `homepage`
  counts as a change and rewrites identical bytes.
- **Probing versions for real: use the bucket wrapper, with a token.**
  Symptom: `Cannot bind parameter because parameter 'Dir' is specified more than
  once`, or every `api.github.com` URL is reported invalid.
  Cause: `bin/checkver.ps1` in the bucket already forwards `-Dir $dir`, and
  Scoop's `Get-GitHubToken` reads `$env:SCOOP_GH_TOKEN` / `scoop config GH_TOKEN`
  -- not `GITHUB_TOKEN` -- so unauthenticated API calls hit 60/h.
  Action: `$env:SCOOP_GH_TOKEN = (gh auth token)`, then `.\bin\checkver.ps1`
  with no `-Dir`, redirecting `*> $out` because the PowerShell tool drops stdout;
  the file is UTF-16, so decode it before reading. Expect two to four apps per
  run to die with `WebClient 请求期间发生异常` -- this network does that.
- **GitHub's own `digest` is the hash source, so nothing needs downloading.**
  Symptom: none -- this is the cheap path.
  Cause: `get_hash_for_app` runs
  `$..assets[?(@.browser_download_url == '<url>')].digest` against
  `api.github.com/repos/o/r/releases` for every `releases/download/` URL, and
  `sha256:<hex>` normalises to the bare digest.
  Action: pre-fill `hash` from the API instead of downloading a 600 MB
  installer, then spend the download on `7z l` instead: the inner payload name
  differs per version and per architecture (`app-64.7z` on x64 but
  `app-arm64.zip` on arm64 in `aionui` 2.2.2), and only listing the installer
  proves a manifest's `installer.script` still matches.
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
