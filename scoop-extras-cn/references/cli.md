# Command-line reference

`python scripts/scoop_manifest.py <command> [options]`, runnable from any cwd.
`SKILL.md` states the rules; this file states the flags.

## The three commands

| Command | Alias | Job | Options |
| :--- | :--- | :--- | :--- |
| **generate** | `gen` | Build a manifest from a recipe and fill it in, optionally sync README | `--list-recipes`, `--from`, `--recipe`, `--fetch-hash`, `--hash-from-file`, `--section`, `--dry-run` |
| **update** | `upd` | Edit fields / bump version + rewrite URLs / recompute hashes / probe upstream | `--name`, `--all`, `--set`, `--unset`, `--version`, `--rehash`, `--checkver [--apply]` |
| **lint** | `check` | Run the 23 rules, repair formatting | `--name`, `--json`, `--strict`, `--fix-format`, `--rules` |

Shared option `--repo <bucket repo root>` overrides the target. It is accepted
before or after the subcommand. Without it the script takes
`$env:Scoop/buckets/extras-cn` whenever that is a bucket repo, and otherwise
walks up from the cwd looking for a directory holding both `bucket/` and
`README.md`. A `--repo` that is not a bucket root is rejected rather than
trusted.

`gen`'s recipe parameters (`--desc`, `--homepage`, `--license`, `--url64`,
`--shortcut-exe`, ...) are per recipe, so they are not listed above:
`--list-recipes` prints them for the recipe you named, and each one is
documented in `references/recipes.md`.

## generate

```bash
python scripts/scoop_manifest.py gen --name myapp --recipe github-nsis-7z \
  --version 3.4.5 --desc "Super app for testing the generator" \
  --homepage https://github.com/o/r --license MIT \
  --url64 "https://github.com/o/r/releases/download/v3.4.5/app.exe#/dl.7z" \
  --repo-url https://github.com/o/r \
  --shortcut-exe app.exe --shortcut-name "MyApp" \
  --section "外语学习" --dry-run

python scripts/scoop_manifest.py gen --from specs.json --section "外语学习"
```

`--from` reads a spec file, which suits batches: an object or an array of
objects whose keys are the `param_docs` names from `recipes.jsonc`, plus
`name`, `recipe` and `section`. Command-line options win over the file.

`--list-recipes` prints when each recipe applies, the required and optional
parameters, and same-kind samples (from this repo where a manifest of that shape
exists, from the upstream bucket otherwise).

Three ways to obtain the hash, **never invented**: `--fetch-hash` streams the
download and computes it; `--hash-from-file <path>` uses a package already on
disk; if neither is given, run `bin/checkhashes.ps1` afterwards (the command
prints that hint).

Rhythm: `--dry-run` to preview, then drop it to write and sync the README, then
`lint --name <app>` to confirm.

## update

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
**The `{"script": ...}` form needs a Scoop environment and explicitly reports
that it cannot probe offline**; use `bin/checkver.ps1` instead. The manifest
side of each form is tabulated in the "checkver forms" section of
`references/manifest-fields.md`.

`--print-json` dumps the result instead of writing it, `--dry-run` previews, and
`--force` lets a change through despite error-level findings.

## lint

```bash
python scripts/scoop_manifest.py lint                  # full run, about 1 second
python scripts/scoop_manifest.py lint --name douyin    # a single app
python scripts/scoop_manifest.py lint --json           # machine-readable report
python scripts/scoop_manifest.py lint --strict         # warnings fail too
python scripts/scoop_manifest.py lint --fix-format     # formatting only
python scripts/scoop_manifest.py lint --rules          # print the rule catalog
```

`--fix-format` touches formatting only (indent / CRLF / trailing newline) and
never JSON semantics.

Exit code: error-level findings give 1; warnings alone give 0, or 1 with
`--strict`. What each rule means, and how to fix it, is in
`references/lint-rules.md`.

## Related files

- Rules and limits, and what this skill refuses to do: `SKILL.md`
- When each recipe applies, and what it emits: `references/recipes.md`
- Manifest fields, checkver forms, canonical key order:
  `references/manifest-fields.md`
- Lint rules and their fixes: `references/lint-rules.md`
