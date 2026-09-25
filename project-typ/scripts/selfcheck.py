#!/usr/bin/env python3
"""Self-check for the project-typ skill package.

Standard library only, offline, one command:

    python selfcheck.py
    python selfcheck.py --list

Five groups, each one an invariant that would otherwise only be caught by a
human rereading the files:

    identity    frontmatter keys, `name` against the directory, the type line
    docs        every `references/` pointer resolves, and nothing is orphaned
    symbols     the symbol list in section 1.1 against references/packages.md
    sections    `## N.` / `### 1.N` numbering, and the rule count the text claims
    size        whether the body is over the soft limit, and the closing note

The `code/*.py` tools quoted in the body belong to the lectures repo, not to
this package, so nothing here runs them. What this package can round-trip
offline is `symbols` (body against the reference doc) and `sections` (the text
against its own numbering).

Exit code 0 when clean, 1 when a check reported something, 2 when the package
itself cannot be read. Report-only -- nothing is ever rewritten.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
SKILL_MD = PACKAGE / "SKILL.md"
REFERENCES = PACKAGE / "references"

FRONTMATTER_END = "\n---"
REQUIRED_KEYS = ("name", "description")
ALLOWED_KEYS = frozenset(
    {"name", "description", "agent_created", "disable-model-invocation"}
)
TYPE_WORDS = ("约束型", "流程型", "混合型")
PACKAGE_NAMES = ("qooklet", "touying-quick", "theorion")

# 软门槛：5000 token / 500 行。估算口径与 docs/skill-review.md 一致（bytes / 3.5）。
TOKEN_BYTES_PER_TOKEN = 3.5
TOKEN_LIMIT = 5000
LINE_LIMIT = 500
SIZE_TOLERANCE = 0.05
SIZE_SECTION = "篇幅说明"
CHECKLIST_SECTION = "检查清单"
SYMBOLS_SECTION = "### 自定义函数"
RULE_SECTION = "条硬规则"

KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):", re.MULTILINE)
NAME_RE = re.compile(r"^name:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
REF_POINTER_RE = re.compile(r"references/[A-Za-z0-9._-]+\.[A-Za-z0-9]+")
CALL_RE = re.compile(r"`([A-Za-z][A-Za-z0-9_.-]*)\([^`]*\)`")
RULE_HEADING_RE = re.compile(
    r"^## [^\n]*?([一二三四五六七八九十]+)条硬规则", re.MULTILINE
)
RULE_COUNT_RE = re.compile(r"([一二三四五六七八九十]+)条硬规则")
H3_RE = re.compile(r"^### ", re.MULTILINE)
CHECKLIST_ITEM_RE = re.compile(r"^- \[ \]", re.MULTILINE)
SIZE_CLAIM_RE = re.compile(r"(\d+)\s*行\s*/\s*估算\s*~([\d.]+)k token")
ANY_H2_RE = re.compile(r"^## ", re.MULTILINE)
CN_NUMERALS = dict(zip("一二三四五六七八九十", range(1, 11), strict=True))


def _read(path: Path) -> str | None:
    """Read UTF-8 text, or None when the file cannot be read at all.

    The two failure modes stay in separate clauses on purpose: at
    ``target-version = "py314"`` a formatter rewrites ``except (A, B):`` into the
    bare PEP 758 form, which only parses on 3.14+.
    """
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
    except UnicodeDecodeError:
        return None


def _split_frontmatter(source: str) -> tuple[str, str] | None:
    """Return (frontmatter, body), or None when the block is missing or unclosed."""
    if not source.startswith("---"):
        return None
    end = source.find(FRONTMATTER_END, 3)
    if end == -1:
        return None
    return source[3:end], source[end + len(FRONTMATTER_END) :]


def _section(source: str, start: str) -> str:
    """Slice from the heading that contains `start` to the next heading at any level."""
    index = source.find(start)
    if index == -1:
        return ""
    rest = source[index + len(start) :]
    stop = re.search(r"^#{2,3} ", rest, re.MULTILINE)
    return rest[: stop.start()] if stop else rest


def _h2_section(source: str, keyword: str) -> str:
    """Slice the whole `## ...keyword...` section, up to the next `##` heading."""
    match = re.search(rf"^## [^\n]*{re.escape(keyword)}[^\n]*$", source, re.MULTILINE)
    if match is None:
        return ""
    rest = source[match.end() :]
    stop = ANY_H2_RE.search(rest)
    return rest[: stop.start()] if stop else rest


def check_identity(source: str) -> list[str]:
    """Frontmatter keys, `name` against the directory name, and the type line."""
    parts = _split_frontmatter(source)
    if parts is None:
        return ["SKILL.md: frontmatter is missing or not closed"]
    block, body = parts
    found: list[str] = []
    keys = KEY_RE.findall(block)
    extra = [key for key in keys if key not in ALLOWED_KEYS]
    if extra:
        found.append(
            "SKILL.md: frontmatter keys outside the allowed set: " + ", ".join(extra)
        )
    missing = [key for key in REQUIRED_KEYS if key not in keys]
    if missing:
        found.append("SKILL.md: frontmatter is missing: " + ", ".join(missing))
    match = NAME_RE.search(block)
    if match is None:
        found.append("SKILL.md: frontmatter is missing name")
    else:
        name = match.group(1).strip().strip("\"'")
        if name != PACKAGE.name:
            found.append(
                f"SKILL.md: name {name!r} does not match the directory "
                f"{PACKAGE.name!r}, so the skill will not load"
            )
    head = "\n".join(body.splitlines()[:12])
    if "技能类型" not in head:
        found.append("SKILL.md: the body does not state 技能类型 near the top")
    elif not any(word in head for word in TYPE_WORDS):
        found.append("SKILL.md: the type line names none of " + " / ".join(TYPE_WORDS))
    return found


def check_docs(source: str) -> list[str]:
    """Every `references/` pointer resolves, and no reference file is orphaned."""
    pointed = set(REF_POINTER_RE.findall(source))
    on_disk = (
        {f"references/{path.name}" for path in REFERENCES.iterdir() if path.is_file()}
        if REFERENCES.is_dir()
        else set()
    )
    found = [
        f"SKILL.md: points at {rel}, which does not exist"
        for rel in sorted(pointed - on_disk)
    ]
    found += [
        f"SKILL.md: never points at {rel}, so nothing loads it"
        for rel in sorted(on_disk - pointed)
    ]
    return found


def check_symbols(source: str) -> list[str]:
    """The symbols the reuse subsection tells the agent to reuse must exist in packages.md.

    Only `name(...)` inside backticks is taken, so native Typst calls quoted
    elsewhere in the body (``image()``, ``read()``) never enter the comparison.
    """
    section = _section(source, SYMBOLS_SECTION)
    if not section:
        return [
            (
                f"SKILL.md: the {SYMBOLS_SECTION} subsection is missing, "
                "so the symbol list has no source"
            )
        ]
    reference = _read(REFERENCES / "packages.md")
    if reference is None:
        return ["references/packages.md: cannot be read as UTF-8"]
    found = [
        (
            f"SKILL.md {SYMBOLS_SECTION} reuses `{name}()` but "
            f"references/packages.md never names it"
        )
        for name in sorted(set(CALL_RE.findall(section)))
        if name not in reference
    ]
    for name in PACKAGE_NAMES:
        if name not in section:
            found.append(f"SKILL.md {SYMBOLS_SECTION} never names the package {name}")
        if name not in reference:
            found.append(f"references/packages.md never names the package {name}")
        elif re.search(rf"^## {re.escape(name)}\b", reference, re.MULTILINE) is None:
            found.append(
                f"references/packages.md has no `## {name}` section of its own"
            )
    return found


def check_sections(source: str) -> list[str]:
    """The claimed rule count is real, the lists are in place, the closing note is last.

    Headings carry no numbering, so the count is read from the heading text
    (`## 六条硬规则`) and checked against the `###` subsections under it.
    """
    found: list[str] = []
    heading = RULE_HEADING_RE.search(source)
    if heading is None:
        return [
            "SKILL.md: no `## N条硬规则` heading, so the rule count cannot be checked"
        ]
    claimed = CN_NUMERALS[heading.group(1)]
    rules = len(H3_RE.findall(_h2_section(source, RULE_SECTION)))
    if claimed != rules:
        found.append(
            f"SKILL.md's rule heading says {claimed} but the section carries "
            f"{rules} `###` subsections"
        )
    mentioned = {CN_NUMERALS.get(word, -1) for word in RULE_COUNT_RE.findall(source)}
    if mentioned != {claimed}:
        found.append(
            f"SKILL.md mentions the rule count as {sorted(mentioned)}, "
            f"the heading says {claimed}"
        )
    checklist = _h2_section(source, CHECKLIST_SECTION)
    if not checklist:
        found.append(f"SKILL.md: no `## ...{CHECKLIST_SECTION}...` section")
    else:
        items = len(CHECKLIST_ITEM_RE.findall(checklist))
        if items < claimed:
            found.append(
                f"SKILL.md: the checklist has {items} items for {claimed} rules"
            )
    if SIZE_SECTION in source and ANY_H2_RE.search(_h2_section(source, SIZE_SECTION)):
        found.append(f"SKILL.md: the {SIZE_SECTION} section is not at the end")
    return found


def check_size(source: str) -> list[str]:
    """The body is over the soft limit, and the closing note says so with real numbers.

    The note is a claim about this very file, so it rots the moment the body
    grows; re-measuring it here is the only way it stays true.
    """
    lines = len(source.splitlines())
    tokens = len(source.encode("utf-8")) / TOKEN_BYTES_PER_TOKEN
    over = lines > LINE_LIMIT or tokens > TOKEN_LIMIT
    has_note = SIZE_SECTION in source
    match = SIZE_CLAIM_RE.search(source)
    if over and not has_note:
        over_claim = (
            f"SKILL.md: {lines} lines / ~{tokens / 1000:.1f}k tokens is over the "
            f"soft limit ({LINE_LIMIT} lines / {TOKEN_LIMIT} tokens) but there is "
            f"no {SIZE_SECTION} section"
        )
        return [over_claim]
    if not over and has_note:
        under_claim = (
            f"SKILL.md: {lines} lines / ~{tokens / 1000:.1f}k tokens is back under "
            f"the soft limit, so the {SIZE_SECTION} section should go"
        )
        return [under_claim]
    if not has_note:
        return []
    if match is None:
        vague = (
            f"SKILL.md: the {SIZE_SECTION} section states no "
            f"「N 行 / 估算 ~X.Xk token」figure, so it cannot be re-measured"
        )
        return [vague]
    found: list[str] = []
    stated_lines = int(match.group(1))
    stated_tokens = float(match.group(2)) * 1000
    if abs(stated_lines - lines) > SIZE_TOLERANCE * lines:
        found.append(
            f"SKILL.md: the {SIZE_SECTION} section claims {stated_lines} lines, "
            f"the file has {lines}"
        )
    if abs(stated_tokens - tokens) > SIZE_TOLERANCE * tokens:
        found.append(
            f"SKILL.md: the {SIZE_SECTION} section claims ~{stated_tokens / 1000:.1f}k "
            f"tokens, the file measures ~{tokens / 1000:.1f}k"
        )
    return found


CHECKS: tuple[tuple[str, Callable[[str], list[str]]], ...] = (
    ("identity", check_identity),
    ("docs", check_docs),
    ("symbols", check_symbols),
    ("sections", check_sections),
    ("size", check_size),
)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["--list"]:
        for check_id, _ in CHECKS:
            print(check_id)
        return 0
    if args:
        print(f"usage: {Path(__file__).name} [--list]", file=sys.stderr)
        return 2
    source = _read(SKILL_MD)
    if source is None:
        print(f"cannot read {SKILL_MD}", file=sys.stderr)
        return 2
    findings = [
        f"[{check_id}] {message}"
        for check_id, check in CHECKS
        for message in check(source)
    ]
    for message in findings:
        print(message)
    if findings:
        print(f"\n{len(findings)} finding(s)", file=sys.stderr)
        return 1
    print(f"all {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
