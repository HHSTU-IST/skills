#!/usr/bin/env python3
"""Check LaTeX math in a file against this skill's house style.

The rule table below is the mechanical twin of the table in `SKILL.md`: same ids,
same meanings. Report-only -- the file is never rewritten.

    python check_style.py <file>...
    python check_style.py --selfcheck

`--selfcheck` is this package's self-check entry. The sibling packages ship a
`scripts/selfcheck.py`; this one has no separate script, so the entry lives
here. `--list-rules` is the same flag under its older name: it prints the rule
table and audits it against `SKILL.md` in both directions, so a rule added on
one side only is a loud failure instead of a silent drift.

Exit code 0 when clean, 1 when a finding was printed, 2 on a usage or rules-table
problem.
"""

from __future__ import annotations

import argparse
import re
import sys
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path

SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"

MATH_FENCE_LANGS = frozenset({"latex", "tex", "math", "katex"})
TEX_SUFFIXES = frozenset({".tex", ".sty", ".cls"})

FENCE_RE = re.compile(r"(?:`{3,}|~{3,})")
SPAN_RE = re.compile(
    r"\$\$(?P<display>.+?)\$\$"
    r"|\$(?P<inline>[^$\n]+?)\$"
    r"|\\\((?P<paren>.+?)\\\)"
    r"|\\\[(?P<bracket>.+?)\\\]",
    re.DOTALL,
)
COMMENT_RE = re.compile(r"(?<!\\)%.*")
INFO_SPLIT_RE = re.compile(r"[\s,{]")


@dataclass(frozen=True)
class Rule:
    """One house-style rule; the id is shared with the table in SKILL.md."""

    id: str
    prefer: str
    patterns: tuple[str, ...]


RULES: tuple[Rule, ...] = (
    Rule(
        "array",
        "按语义换成 gathered / gather / aligned / cases / vmatrix / bmatrix",
        (r"\\begin\{array\}",),
    ),
    Rule(
        "bigg",
        "显式定尺寸：\\big / \\Big / \\bigg / \\Bigg",
        (r"\\(?:left|right)(?![A-Za-z])",),
    ),
    Rule(
        "underset-slots",
        "两个参数位都写全：\\underset{w}{\\mathrm{argmin}}，空位留空花括号",
        (r"\\(?:under|over)set\{(?:[^{}]|\{[^{}]*\})*\}(?!\s*\{)",),
    ),
    Rule("transpose", "写 ^{\\top}", (r"\^(?:\{\s*T\s*\}|T(?![A-Za-z]))",)),
    Rule("limit-arrow", "写 \\to", (r"\\rightarrow(?![A-Za-z])",)),
    Rule("underset-limits", "写 \\underset{}{} / \\overset{}{}", (r"\\limits\s*[_^]",)),
    Rule(
        "mathrm",
        "写 \\mathrm{}",
        (r"\\rm(?![A-Za-z])", r"\\mathop(?![A-Za-z])", r"\\operatorname(?![A-Za-z])"),
    ),
    Rule("mathbf", "写 \\mathbf{}", (r"\\bf(?![A-Za-z])",)),
    Rule("mathit", "写 \\mathit{}", (r"\\it(?![A-Za-z])",)),
)


@dataclass(frozen=True)
class Region:
    """A half-open span of the source that holds math."""

    start: int
    end: int


def _mask_fences(text: str) -> tuple[str, list[Region]]:
    """Blank the non-math fenced blocks; hand back the math-fenced ones as regions.

    Blanking keeps the character offsets intact, so a finding still maps back to the
    right line and column.
    """
    chars = list(text)
    regions: list[Region] = []
    marker = ""
    math_fence = False
    body_start = 0
    pos = 0
    for line in text.splitlines(keepends=True):
        found = FENCE_RE.match(line.strip())
        if not marker and found is not None:
            info = line.strip()[len(found.group(0)) :].strip()
            marker = found.group(0)[0] * 3
            math_fence = (
                INFO_SPLIT_RE.split(info, maxsplit=1)[0].lower() in MATH_FENCE_LANGS
            )
            body_start = pos + len(line)
        elif marker:
            if found is not None and found.group(0)[0] == marker[0]:
                if math_fence:
                    regions.append(Region(body_start, pos))
                marker = ""
            elif not math_fence:
                for index in range(pos, pos + len(line)):
                    if chars[index] != "\n":
                        chars[index] = " "
        pos += len(line)
    if marker and math_fence:
        regions.append(Region(body_start, pos))
    return "".join(chars), regions


def _regions(text: str, *, whole_file: bool) -> tuple[str, list[Region]]:
    """Return the text with non-math code blanked, plus the spans that count as math."""
    if whole_file:
        masked = COMMENT_RE.sub(lambda match: " " * len(match.group(0)), text)
        return masked, [Region(0, len(masked))]
    masked, fence_regions = _mask_fences(text)
    spans = [Region(*match.span()) for match in SPAN_RE.finditer(masked)]
    return masked, sorted(fence_regions + spans, key=lambda region: region.start)


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for index, char in enumerate(text):
        if char == "\n":
            starts.append(index + 1)
    return starts


def check_file(path: Path) -> list[str]:
    """Return one line per finding, empty when the file is clean."""
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{path}: not UTF-8 text"]
    except OSError as exc:
        return [f"{path}: cannot read: {exc}"]
    masked, regions = _regions(raw, whole_file=path.suffix.lower() in TEX_SUFFIXES)
    starts = _line_starts(raw)
    hits: dict[int, tuple[str, str, str]] = {}
    for rule in RULES:
        for pattern in rule.patterns:
            compiled = re.compile(pattern)
            for region in regions:
                for match in compiled.finditer(masked, region.start, region.end):
                    hits.setdefault(
                        match.start(), (rule.id, rule.prefer, match.group(0))
                    )
    report: list[str] = []
    for offset in sorted(hits):
        rule_id, prefer, found = hits[offset]
        row = bisect_right(starts, offset) - 1
        snippet = " ".join(found.split())
        report.append(
            f"{path}:{row + 1}:{offset - starts[row] + 1}: [{rule_id}] {snippet}  ->  {prefer}"
        )
    return report


TABLE_HEADING_RE = re.compile(
    r"^##\s*规则表\s*$(?P<body>.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL
)
TABLE_ROW_RE = re.compile(r"^\|\s*`(?P<id>[^`]+)`", re.MULTILINE)


def table_drift(doc: str) -> tuple[list[str], list[str]]:
    """Compare `RULES` against the rule table in `SKILL.md`.

    Returns `(missing, extra)`:

    - `missing`: a rule the script has but the table never documents. The search
      is lenient -- the id may appear anywhere in the file, not just the table.
    - `extra`: an id the table lists but no rule implements. Read from the
      `## 规则表` section alone, so the report names the exact row to delete.

    Either list being non-empty means the two sides have drifted apart.
    """
    missing = [rule.id for rule in RULES if f"`{rule.id}`" not in doc]
    match = TABLE_HEADING_RE.search(doc)
    listed = sorted(set(TABLE_ROW_RE.findall(match.group("body")))) if match else []
    known = {rule.id for rule in RULES}
    extra = [rule_id for rule_id in listed if rule_id not in known]
    return missing, extra


def list_rules() -> int:
    """Print the rule table, then audit it against SKILL.md in both directions."""
    width = max(len(rule.id) for rule in RULES)
    for rule in RULES:
        print(f"{rule.id:<{width}}  {rule.prefer}")
    try:
        doc = SKILL_MD.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"\n! cannot read SKILL.md next to this script: {exc}", file=sys.stderr)
        return 2
    missing, extra = table_drift(doc)
    if missing:
        print(f"\n! SKILL.md's table is missing: {', '.join(missing)}", file=sys.stderr)
    if extra:
        print(
            "! SKILL.md's table lists ids with no rule in this script: "
            f"{', '.join(extra)}",
            file=sys.stderr,
        )
    if missing or extra:
        return 2
    print(f"\nall {len(RULES)} rule ids match SKILL.md's table, both ways")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("paths", nargs="*", type=Path, help="files to check")
    parser.add_argument(
        "--selfcheck",
        "--list-rules",
        dest="selfcheck",
        action="store_true",
        help="self-check: print the rule table and audit it against SKILL.md",
    )
    args = parser.parse_args(argv)
    if args.selfcheck:
        return list_rules()
    paths: list[Path] = args.paths
    if not paths:
        parser.error("give at least one file to check")
    findings: list[str] = []
    for path in paths:
        if path.is_file():
            findings.extend(check_file(path))
        else:
            findings.append(f"{path}: not a file")
    for line in findings:
        print(line)
    if findings:
        print(
            f"\n{len(findings)} finding(s); see SKILL.md for what to write instead",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
