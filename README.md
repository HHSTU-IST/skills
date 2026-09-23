# skills

[中文版](README.zh.md)

A collection of [WorkBuddy](https://www.workbuddy.cn) Agent Skills.

Each skill is a self-contained package: a `SKILL.md` that the model loads on demand, plus `scripts/` (deterministic code), `references/` (long specs, read only when needed) and `assets/` (templates and data that never enter context). A skill's `name` in its frontmatter must equal its directory name, or it will not load.

This repo is the single source of truth. Skills that are "installed" are junctions under `~/.workbuddy/skills/` pointing back here, so edits land in the repo and version control stays meaningful.

## Contents

| Group | Skill | One line |
| :--- | :--- | :--- |
| Tooling | [`skill-draft`](#skill-draft) | Build a skill package and gate every file in it |
| Project conventions | [`project-py`](#project-py) | Python: package manager, style, ruff + ty |
| Project conventions | [`project-typ`](#project-typ) | Typst lecture slides: assets, layout, compile |
| Scoop buckets | [`scoop-main-plus`](#scoop-main-plus) | Manifests for the Main-Plus bucket |
| Scoop buckets | [`scoop-extras-plus`](#scoop-extras-plus) | Manifests for the Extras-Plus bucket |
| Scoop buckets | [`scoop-extras-cn`](#scoop-extras-cn) | Manifests for the Extras-CN bucket |

## Tooling

### skill-draft

Turn a workflow or a piece of domain knowledge into a Skill package, and make every file in it pass a quality gate **before it lands on disk**.

The iron rule is that a file is not done until the gate passes, and the gate is re-run immediately after every write. One command drives everything:

```bash
python <this skill dir>/scripts/verify.py <file-or-dir>...
```

Every file type gets a three-stage pipeline — builtin check, repair, verify — and the verify stage must exit zero. Coverage today:

| Type | Tools |
| :--- | :--- |
| `.py` | ruff + ty, plus in-process syntax compilation |
| `.md` | rumdl |
| `.json` / `.jsonc` | parse validation |
| `.ts` / `.js` family | oxlint + oxfmt |
| `.css` / `.scss` / `.less` | oxfmt |
| `.png` | oxipng + a chunk/CRC integrity recheck |

Adding a file type normally means editing `scripts/file-types.json` only, with no code change; in-process checks go into `scripts/checkers.py`. The package uses the Python standard library and nothing else, so it runs on any machine.

`SKILL.md` also carries a long "gate details" section recording the traps that cost real debugging time — why `oxlint` needs `--deny-warnings`, why `oxipng`'s exit code cannot be trusted, why a `.jsonc` name is sometimes deliberate rather than a typo.

## Project conventions

These two encode house rules for a separate lectures repository. They are passive: they describe conventions, they do not run anything.

### project-py

Rules for writing `.py` source. Notebooks are explicitly out of scope.

- **Package manager is a hard gate.** `pip install` is forbidden. Dependencies change only through `micromamba` or `uv`, and the choice is settled with the user first — with `micromamba`, the specific environment name is asked for before anything runs.
- **Style.** Iterate with `enumerate()` / `zip()`, never `range(len())`; Matplotlib through the object-oriented interface with `constrained_layout=True`; batch decorations through `ax.set(...)` and pass spines as one list.
- **Static checking order is fixed: format → check → ty.** Formatting is not optional, because `ruff check` passing says nothing about formatting. `ty` must be pointed at an interpreter that actually has the dependencies, or it floods the output with false `unresolved-import` alarms.
- **No absolute paths and no pinned version numbers** anywhere in docs, scripts or config — including `ty.toml`. Both are resolved at run time, since a hard-coded path turns into wrong information the moment the machine changes.

`references/toolchain.md` holds the command cookbook and the isolation notes.

### project-typ

Rules for writing and editing Typst lecture decks.

- **Check the packages before writing a helper.** Before defining any custom function, search `qooklet`, `touying-quick` and `theorion` for an existing implementation — most layout needs (tables, code blocks, callouts, equation numbering, figure references) are already solved, and re-implementing them produces inconsistent typography.
- **All external content lives in files, never inlined.** Code goes to `python/`, `blender/` or `cv40examples/` and comes back through `read()`; images go to `images/` and are wrapped in `figure(image(...), caption: none)`; data goes to `data/`, preferably as CSV, and feeds `tableq(data, k)`. Paths are always relative to the repository root.
- **Layout.** Fixed-height two-column blocks use `columns()` with an explicit `#colbreak()` between the panes, each pane wrapped in its own `#[ … ]` — dropping the `#colbreak()` silently changes the layout, because `columns()` is flowing rather than positioned.
- **Prose is not to be chopped up.** Long Chinese sentences stay intact; clause breaks use commas and semicolons, not periods.
- **Don't show the PDF.** Compiling is for verification only. Report the conclusion — whether it built, which line failed, which pages `slide_qa.py` flagged — instead of pushing a PDF into the user's editor.

`references/packages.md` documents the exported symbols of the three packages; `references/syntax.md` collects high-frequency Typst patterns and pitfalls.

## Scoop buckets

Three sibling skills that turn "upstream shipped something new" or "upstream shipped a new version" into a single command. They share an architecture: a recipe catalog, a shared library, a three-command CLI, a self-check, and a rule engine that validates the result before it is written.

They differ only where their target repositories force them to. The extras builds are the same skill ported to two buckets with different README conventions and different dominant package shapes; `scoop-extras-cn` additionally documents its divergence from `scoop-extras-plus` in its own `SKILL.md`.

| | `scoop-main-plus` | `scoop-extras-plus` | `scoop-extras-cn` |
| :--- | :--- | :--- | :--- |
| Target bucket | `$Scoop/buckets/main-plus` | `$Scoop/buckets/extras-plus` | `$Scoop/buckets/extras-cn` |
| Recipes | 18 | 16 | 16 |
| Lint rules | 22 | 22 | 22 |
| README language | English | English | Chinese |

**Common shape of each.** All three expose the same three trigger commands:

| Command | Alias | Job |
| :--- | :--- | :--- |
| `generate` | `gen` | Build a manifest from a recipe and fill it in |
| `update` | `upd` | Edit fields, bump the version, recompute hashes, probe upstream |
| `lint` | `check` | Run the rule catalog and repair formatting |

Everything runs offline except `--checkver`, `--fetch-hash` and `--rehash`. Python standard library only, so any Python 3.11+ works. The scripts derive the package root themselves and run from any working directory.

### Shared guarantees

- **The bucket root is resolved at run time**, never baked in. The expansion order is `--repo <path>`, then a walk up from the current directory, then the bucket's own installed copy under `$Scoop`. No file in any package stores an expanded Scoop path, and the self-check fails if a literal reappears.
- **The rule engine runs before the write.** Error-level findings block it; `--force` overrides. `--dry-run` previews, `--print-json` dumps the result.
- **Existing key order is preserved.** `update` only slots *new* fields into their canonical position; a full reorder needs an explicit `--reorder`.
- **Hashes are never invented.** Either `--fetch-hash` streams the download and computes it, `--hash-from-file` uses a package already on disk, or the run prints the hint to follow up with `bin/checkhashes.ps1`.
- **The README is controlled.** Syncing touches only the summary tables it recognises and leaves every other column byte-identical. A missing section skips the sync with an explanation rather than mangling the file.
- **32bit is not supported.** `arch` accepts `64bit` and `arm64` only, so `url32` / `hash32` are neither accepted nor emitted.

The write target is always `<repo>/bucket/<app>.json` plus the README row; `bin/`, `scripts/` and `.github/` belong to Scoop and to each repo's CI and are never touched.

### scoop-main-plus

Manifests for the **Main-Plus** bucket, which is bin-first: 39 of its 40 packages install through `bin` and it declares no `shortcuts` at all. A shortcut is the exception and signals that the package is not really a CLI tool. The bucket resolves to `$Scoop/buckets/main-plus` from any working directory when no `--repo` is given.

`generate` settles six questions up front — upstream, what ships, version, what goes on PATH, whether a shortcut is genuinely wanted, and the implementation language for the README — and asks rather than guesses. This bucket emits canonical key order, uses `--flat-url` to collapse a single-architecture `architecture` block, and documents the population evidence behind each of its 18 recipes in `references/coverage.md`.

### scoop-extras-plus

Manifests for the **Extras-Plus** bucket (56 manifests, English-facing). Sixteen recipes; the README carries one `## ⭐️ Summary` table across five `###` sections with the three columns `App / Auto-Update ? / Note`.

Baseline: **0 error-level findings** anywhere in the bucket. `lint` prints live counts rather than a frozen number, because the bucket grows with every autoupdate commit. `SKILL.md` lists the real issues found so far, each tagged with the rule that caught it — a version pinned in the URL that no longer matches `version`, an `md5:` hash prefix Scoop does not accept, and a few README spellings that drifted from the manifest name.

### scoop-extras-cn

Manifests for the **Extras-CN** bucket (88 manifests, Chinese-facing). Same recipe catalog, same builders, same canonical key order as the Extras-Plus build; the differences are the ones this bucket actually forces, and `SKILL.md` tabulates all of them.

What makes this one distinct:

- **Bilingual descriptions.** 57 of 88 manifests use Chinese, so rules that enforce English phrasing stand down for any string containing CJK — and the trailing-period check with them, since a Chinese sentence legitimately ends with `。`.
- **A four-column README** (`中文名称` before `App`) with CJK cells padded to display width, split across `跨平台` / `Win 专属` / `开源镜像`, plus a two-column plain-text mirror table.
- **A rule that was dead code elsewhere.** The README check was gated on the literal English heading `## ⭐️ Summary`, which this repo spells `## ⭐️ 总结`, so it never fired. Re-gated on "the README has summary tables", it surfaced 35 findings that split cleanly into 17 stable-convention entries and 18 genuine README gaps — a good illustration of why a check nobody can pass is worse than no check.

Two upstream rule fixes were carried into this build because they are latent bugs rather than repo-specific choices: the `jsonpath` / `xpath` regex requirement, and a recursive-delete pattern that was over-escaped and could never match.

## Working on a skill

Each skill validates itself offline:

```bash
python scripts/sm_selftest.py            # Scoop skills: full self-check
python scripts/verify.py .               # skill-draft: gate every file
```

The self-checks are not decoration. They enforce recipe ↔ builder coverage both ways, docs ↔ code consistency (the lint-rule table must match the code word for word), round-trip serialization against the real bucket, README sync idempotence, and the rule that a skill's `name` equals its directory name.

### Two conventions worth knowing before you edit

**Never add a `.json` data file to a Scoop skill.** The bucket CI validates every *changed* `.json` in the repository against Scoop's manifest schema — repo-wide, because the changed-file listing ignores its path filter. A non-manifest `.json` inside a skill turns CI red. That is why the recipe catalog ships as `assets/recipes.jsonc`: the `.jsonc` name is a deliberate dodge, and its content stays strict JSON rather than using comments.

**Never write a machine-local absolute path into a skill.** Packages get copied and ported, and a hard-coded path becomes wrong the moment it is copied. Refer to the skill itself with the `<this skill dir>` placeholder and to the home directory with `~`, and resolve tool and environment locations at run time. `skill-draft`'s `no-local-paths` check backstops this.
