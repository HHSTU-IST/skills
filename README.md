# skills

[中文版](README.zh.md)

A collection of my daily Agent Skills.

Each skill is a self-contained package: a `SKILL.md` that the model loads on demand, plus `scripts/` (deterministic code), `references/` (long specs, read only when needed) and `assets/` (templates and data that never enter context). A skill's `name` in its frontmatter must equal its directory name, or it will not load.

This repo is the main working copy. A skill becomes available to WorkBuddy once it sits in a skills directory the app scans, and the two candidate locations differ in scope:

| Level   | Path                                  | Availability                                                   |
| :------ | :------------------------------------ | :------------------------------------------------------------- |
| User    | `~/.workbuddy/skills/<name>/`         | Every project on this machine                                  |
| Project | `<project>/.workbuddy/skills/<name>/` | That project only, and shared with anyone who gets the project |

A skill's directory name and its frontmatter `name` must match, or it will not load.

## Installing a skill

### Put the package where the app looks

The simplest install is a copy — WorkBuddy scans the directory tree on each launch, so a plain copy works with no further steps:

```bash
cp -r <skill> ~/.workbuddy/skills/<skill>            # user level, all projects
cp -r <skill> <project>/.workbuddy/skills/<skill>    # project level, that repo only
```

To keep one editable copy instead, link to it rather than copying:

```powershell
# Windows: a directory junction needs no administrator rights
New-Item -ItemType Junction -Path "$env:USERPROFILE\.workbuddy\skills\<skill>" -Target "<repo>\<skill>"
```

```bash
# macOS / Linux
ln -s "<repo>/<skill>" ~/.workbuddy/skills/<skill>
```

### Install with npx

For a skill that already lives in a public Git repository or on a marketplace, the `skills` CLI does the fetch and the placement in one step, so nothing has to be copied by hand:

```bash
npx skills find "keyword"                        # search interactively
npx skills add <owner>/<repo> -g -y              # every skill in a repo, user level
npx skills add <owner>/<repo>@<skill-name> -g -y # one named skill
npx skills add <owner>/<repo> -y                 # project level (the default)
npx skills list                                  # show what is installed
npx skills update                                # pull later versions
npx skills remove <skill>                        # uninstall
```

The flags worth knowing: `-g` / `--global` installs to `~/.workbuddy/skills/` instead of the project, `-y` / `--yes` skips the confirmation prompt, `-s` / `--skill` picks skills by name, `-a` / `--agent` targets specific agents, `--copy` copies files where the default would symlink, and `--list` (`-l`) only prints what a repository offers without installing anything. Combination form: `npx skills add <owner>/<repo> --all` is shorthand for `--skill '*' --agent '*' -y`.

Two limits apply to this route. It needs network access to GitHub — behind a firewall it stalls at `Cloning repository…` and eventually fails on port 443, which is a proxy problem rather than a skill problem — and it only installs packages that exist upstream on GitHub or in a marketplace. The skills in this repo are not published there, so for this repo the copy or link route above is the one that applies; `npx skills init <name>` is the useful part here, since it lays out a skeleton package you can then fill in.

### From the marketplace

Skills that are published to a marketplace are installed from the WorkBuddy UI, or through `npx skills add` as above, instead of by hand. This repo is not published, so the manual route is the one that applies to it.

### Verify before you trust it

Run the package's own check after installing. Every skill here is self-validating and offline:

```bash
python <installed skill>/scripts/sm_selftest.py    # Scoop skills
python <installed skill>/scripts/verify.py .       # skill-draft
python <installed skill>/scripts/check_style.py --list-rules  # project-tex
```

## Using a skill

None of these skills needs an explicit command to fire. None declares `disable-model-invocation`, so WorkBuddy loads one by matching your wording against the `description` and its trigger words. Two things follow from that: phrasing the request in the vocabulary the skill already lists is what makes it load, and naming the skill outright is the way to force it when a request could plausibly match more than one.

The examples below use each skill's own trigger words. Where a skill wraps a CLI, the invocation it will build is shown too, since knowing the shape of an exact call is often more useful than knowing the trigger phrase.

### skill-draft

Triggers: *create a skill, new skill, write SKILL.md, save this workflow as a skill, edit a skill, validate a skill package, add a file type to the gate.*

```text
Walk through what I just did and save it as a skill.
```

```text
Create a skill for rotating PDF pages, then run the gate on it.
```

```text
Add .toml to the gate's rules table, for taplo.
```

The third one is the extension path: adding a file type normally means editing `scripts/file-types.json` alone, with no code change, and the skill knows that.

### project-py

Triggers: *Python, py, ruff, ty, lint, 类型检查, 包管理, micromamba, uv, matplotlib, subplots.*

```text
Add error bars to these plots and clean up the figure code.
```

```text
I need scipy for the next section — set it up.
```

```text
Lint and type-check the python/ directory.
```

The second is worth noting: this skill will not install anything until it has asked which of `micromamba` / `uv` you want, and which environment by name — `pip install` is refused outright.

### project-tex

Triggers: *LaTeX, latex, tex, 公式, 数学公式, 矩阵, 行列式, 方程组, 分段函数, begin, aligned, bmatrix, vmatrix, mathrm, atop.*

```text
把这段推导整理成多行公式，按语义挑环境。
```

```text
写一下这个分段函数，再配一个矩阵。
```

```text
这段公式检查一下写法。
```

The third is the mechanical half: it runs `python <this skill dir>/scripts/check_style.py <file>`, which is report-only and exits 0 when clean. The script knows Markdown as well as `.tex` — it finds math inside `$…$`, `$$…$$`, `\(…\)`, `\[…\]` and `latex`-fenced blocks, so a lecture note gets the same audit as a source file.

### project-typ

Triggers: *Typst, typ, 讲义, 课件, 幻灯片, touying, qooklet, .typ, figure, tableq, read().*

```text
Add a section on histogram equalisation to the image processing deck.
```

```text
This page overflows — check the layout and fix it.
```

```text
Turn this code sample into a two-column slide with the output image beside it.
```

The two prompts that matter most here are the ones that trip the rules: any request to define a new helper should first get a package search, and the third example must come back as a real file under `python/` reached through `read()`, never inlined into the `.typ`.

### scoop-main-plus

Triggers: *generate manifest, new manifest, update manifest, lint manifest, scoop-main-plus, main-plus, scoop manifest, bucket manifest, checkver, autoupdate, hash verification, version bump, Excavator.*

```text
Add a manifest for the new ripgrep release to main-plus.
```

```text
Bump every package in main-plus and recompute the hashes.
```

```text
Lint the main-plus bucket.
```

Under the hood those become `gen --name <app> --recipe <recipe>`, `upd --all --checkver --apply --rehash`, and `lint`, with the bucket resolved from `$Scoop` when you do not pass `--repo`.

### scoop-extras-plus

Triggers: the same set as main-plus, with *scoop-extras-plus* in place of *main-plus*.

```text
Add a manifest for the new IsoBuster release.
```

```text
Which packages in extras-plus have a version that no longer matches their URL?
```

```text
Sync the README summary table for the packages I just added.
```

The second is a read-only question the lint rules answer directly (`W104`), which is a cheaper way to audit than running a bump.

### scoop-extras-cn

Triggers: the same set plus *scoop-extras-cn* and the Chinese forms *生成 manifest, 更新 manifest, 检查 manifest.*

```text
给 extras-cn 加一个新包，中文名是「飞书」。
```

```text
检查一下 extras-cn 的 README 总结表，哪些包没列进去？
```

```text
把 extras-cn 里所有包检查一遍，并把格式问题修掉。
```

The first exercises the four-column README and the `中文名称` cell that this bucket alone has; the second reaches `W105`, whose hint names the exact spelling it found, which is what makes the display-name-versus-manifest-name mismatch diagnosable without reading the README by hand.

## Contents

| Group               | Skill                                     | One line                                        |
| :------------------ | :---------------------------------------- | :---------------------------------------------- |
| Tooling             | [`skill-draft`](#skill-draft)             | Build a skill package and gate every file in it |
| Project conventions | [`project-py`](#project-py)               | Python: package manager, style, ruff + ty       |
| Project conventions | [`project-tex`](#project-tex)             | LaTeX math: environments, brackets, notation    |
| Project conventions | [`project-typ`](#project-typ)             | Typst lecture slides: assets, layout, compile   |
| Scoop buckets       | [`scoop-main-plus`](#scoop-main-plus)     | Manifests for the Main-Plus bucket              |
| Scoop buckets       | [`scoop-extras-plus`](#scoop-extras-plus) | Manifests for the Extras-Plus bucket            |
| Scoop buckets       | [`scoop-extras-cn`](#scoop-extras-cn)     | Manifests for the Extras-CN bucket              |
