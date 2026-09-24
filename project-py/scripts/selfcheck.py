#!/usr/bin/env python3
"""Self-check for the project-py skill package.

Standard library only, offline, one command:

    python selfcheck.py
    python selfcheck.py --list

Four groups, each one an invariant that would otherwise only be caught by a
human rereading the files:

    identity    frontmatter keys, `name` against the directory, the type line
    docs        every `references/` pointer resolves, and nothing is orphaned
    commands    the flags the body calls mandatory are really on the commands
    pip-guard   no `pip` instruction without a prohibition beside it, and the
                legal entries are actually spelled out

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

KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):", re.MULTILINE)
NAME_RE = re.compile(r"^name:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
BASH_BLOCK_RE = re.compile(
    r"^```bash[ \t]*$\n(?P<body>.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL
)
REF_POINTER_RE = re.compile(r"references/[A-Za-z0-9._-]+\.[A-Za-z0-9]+")
PIP_RE = re.compile(r"\bpip\b")

# One entry per command the body states a rule about, as
# (probe, mode, fragments it must carry, why).
COMMAND_RULES: tuple[tuple[str, str, tuple[str, ...], str], ...] = (
    ("ruff format", "startswith", ("--exclude",), "notebooks have to be excluded"),
    (
        "ruff check",
        "startswith",
        ("--no-fix", "--no-fix-only", "--exclude"),
        "only --no-fix + --no-fix-only keeps check from rewriting the file",
    ),
    ("ty check", "contains", ("micromamba run -n",), "ty needs the chosen env"),
    (
        "rumdl",
        "startswith",
        (PACKAGE.name,),
        "the path must be limited to this package",
    ),
)

# A `pip` mention is legal only when the same paragraph pushes back on it.
NEGATION = (
    "禁止",
    "严禁",
    "不许",
    "不得",
    "不要",
    "不能",
    "不是",
    "不用",
    "没有",
    "不该",
    "不出现",
    "兜底",
    "forbidden",
    "never",
)
# The positive half: the body has to name the entries that *are* allowed.
LEGAL_ENTRY = ("micromamba install", "uv add", "uv run", "uv sync")


def _read(path: Path) -> str | None:
    """Read UTF-8 text, or None when the file cannot be read at all.

    The two failure modes stay in separate ``except`` clauses on purpose: with
    ``target-version = "py314"`` a formatter rewrites ``except (A, B):`` into
    ``except A, B:`` (PEP 758), which only parses on 3.14+.
    """
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
    except UnicodeDecodeError:
        return None


def _package_files() -> list[Path]:
    """Every Markdown file this package ships."""
    files = [SKILL_MD]
    if REFERENCES.is_dir():
        files.extend(sorted(path for path in REFERENCES.iterdir() if path.is_file()))
    return files


def _split_frontmatter(source: str) -> tuple[str, str] | None:
    """Return (frontmatter, body), or None when the block is missing or unclosed."""
    if not source.startswith("---"):
        return None
    end = source.find(FRONTMATTER_END, 3)
    if end == -1:
        return None
    return source[3:end], source[end + len(FRONTMATTER_END) :]


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
    found: list[str] = []
    pointed = set(REF_POINTER_RE.findall(source))
    on_disk = (
        {f"references/{path.name}" for path in REFERENCES.iterdir() if path.is_file()}
        if REFERENCES.is_dir()
        else set()
    )
    for rel in sorted(pointed - on_disk):
        found.append(f"SKILL.md: points at {rel}, which does not exist")
    for rel in sorted(on_disk - pointed):
        found.append(f"SKILL.md: never points at {rel}, so nothing loads it")
    return found


def _carried(required: str, line: str, tokens: list[str]) -> bool:
    """Whether a required fragment is on the line, as a flag where it is one.

    Flags have to be their own token: ``--no-fix`` is a substring of
    ``--no-fix-only``, yet only the pair stops ``ruff check`` from rewriting
    files, so a substring test would bless the unsafe command. Multi-word
    fragments such as ``micromamba run -n`` stay substring matches.
    """
    if required.startswith("-") and " " not in required:
        return required in tokens
    return required in line


def check_commands(source: str) -> list[str]:
    """The mandatory flags are on the commands, not just in the prose beside them."""
    found: list[str] = []
    for block in BASH_BLOCK_RE.findall(source):
        for raw in block.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.split()
            for probe, mode, required, why in COMMAND_RULES:
                hit = line.startswith(probe) if mode == "startswith" else probe in line
                if not hit:
                    continue
                gaps = [item for item in required if not _carried(item, line, tokens)]
                if gaps:
                    found.append(
                        f"SKILL.md: {line!r} is missing {', '.join(gaps)} ({why})"
                    )
    return found


def check_pip_guard(source: str) -> list[str]:
    """No `pip` instruction without a prohibition, and the legal entries shown."""
    found: list[str] = []
    texts: list[str] = []
    for path in _package_files():
        text = source if path == SKILL_MD else _read(path)
        if text is None:
            found.append(f"{path.name}: cannot be read")
            continue
        texts.append(text)
        for block in re.split(r"\n[ \t]*\n", text):
            if not PIP_RE.search(block):
                continue
            if any(word in block for word in NEGATION):
                continue
            line = next(
                (row.strip() for row in block.splitlines() if PIP_RE.search(row)),
                block.strip(),
            )
            found.append(
                f"{path.name}: `pip` with no prohibition in the same paragraph -- "
                f"{line[:70]}"
            )
    if not any(entry in "\n".join(texts) for entry in LEGAL_ENTRY):
        found.append(
            "package: the legal install entries are never spelled out, so the "
            "prohibition has no positive half"
        )
    return found


CHECKS: tuple[tuple[str, Callable[[str], list[str]]], ...] = (
    ("identity", check_identity),
    ("docs", check_docs),
    ("commands", check_commands),
    ("pip-guard", check_pip_guard),
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
