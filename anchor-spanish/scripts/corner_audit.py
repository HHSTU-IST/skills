"""一致性守卫：本技能包「文档 ↔ 配置 ↔ 身份」三者对齐，且不外泄他语言内容。

设计原则：**只看本包**。审计不做任何跨技能包比对（每个语言包是自包含单元），
只保证：

1. 身份：包内**恰好一个**配置，且文件名 == `DEFAULT_CONFIG_NAME`；
   `SKILL.md` frontmatter `name` == `SKILL_NAME` == `meta.skill_name`；
2. 编辑器 schema：`$schema` 指向包内真实存在的 JSON Schema，且配置满足其 `required`；
3. 文档 ↔ 配置：`SKILL.md` 中出现的取值必须与 JSON 一致（版本 / 约束 / 时间
   分配 / 词性分组 / 词汇量 / 等级标签 / 提问编排 / 话题机制）；
4. 内容纯度：包内不得出现其它语言的配置文件名（防止误拷他语言资产）。

任一失败即非零退出。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from corner_config import (
    DEFAULT_CONFIG_NAME,
    LANG,
    SKILL_MD_NAME,
    SKILL_NAME,
    assets_dir,
    skill_root,
)


def config_path() -> Path:
    """本包唯一配置：`<skill>/assets/<DEFAULT_CONFIG_NAME>`。"""
    return assets_dir() / DEFAULT_CONFIG_NAME


def audit_identity(cfg: dict) -> list[str]:
    """包身份校验：一个配置、文件名正确、SKILL.md 与 meta 的名称一致。"""
    fails: list[str] = []
    found = sorted(p.name for p in assets_dir().glob("*-corner-config.json"))
    if found != [DEFAULT_CONFIG_NAME]:
        fails.append(
            f"[{SKILL_NAME}] assets/ 应恰好包含 {DEFAULT_CONFIG_NAME}，实际: {found or '（无）'}"
        )
        if DEFAULT_CONFIG_NAME not in found:
            return fails  # 缺本包配置，后续检查无意义

    md_path = skill_root() / SKILL_MD_NAME
    md = md_path.read_text(encoding="utf-8")
    m = re.search(r"^name:\s*(\S+)", md, re.MULTILINE)
    fm_name = m.group(1) if m else "<none>"
    if fm_name != SKILL_NAME:
        fails.append(
            f"[{SKILL_NAME}] {SKILL_MD_NAME} frontmatter name={fm_name!r} != {SKILL_NAME!r}"
        )
    meta_name = cfg["meta"]["skill_name"]
    if meta_name != SKILL_NAME:
        fails.append(f"[{SKILL_NAME}] meta.skill_name={meta_name!r} != {SKILL_NAME!r}")
    return fails


def audit_schema(cfg: dict) -> list[str]:
    """编辑器 schema：`$schema` 指向包内真实存在的 JSON Schema，且配置满足其 `required`。

    只做「引用可解析 + 顶层必填键齐备」这一层轻量校验（脚本仅依赖标准库，不引入
    JSON Schema 校验器）；取值域的完整校验交给编辑器的 schema 支持。
    """
    tag = f"[{SKILL_NAME}/{LANG}]"
    ref = cfg.get("$schema")
    if not ref:
        return [f"{tag} 配置缺少 $schema，编辑器无法补全 / 校验"]
    if "://" in ref:  # 远端 schema：本包不校验
        return []
    target = (config_path().parent / ref).resolve()
    if not target.is_file():
        return [f"{tag} $schema 指向的文件不存在: {ref!r}"]
    try:
        sch = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{tag} $schema 目标不是合法 JSON: {ref!r}（{exc.msg}）"]
    if not isinstance(sch, dict) or not sch.get("title"):
        return [f"{tag} $schema 目标缺少 title: {ref!r}"]
    missing = [k for k in sch.get("required", []) if k not in cfg]
    if missing:
        return [f"{tag} 配置缺少 schema 要求的顶层键: {', '.join(missing)}"]
    return []


def audit(cfg: dict) -> list[str]:
    """本包「SKILL.md ↔ 配置」逐项比对。"""
    md = (skill_root() / SKILL_MD_NAME).read_text(encoding="utf-8")
    tag = f"[{SKILL_NAME}/{LANG}]"
    fails: list[str] = []

    def need(token: str, what: str) -> None:
        if token not in md:
            fails.append(f"{tag} {what}: 配置值 {token!r} 未出现在 {SKILL_MD_NAME}")

    # 1) 版本号：frontmatter version == meta.version
    m = re.search(r"^version:\s*(\S+)", md, re.MULTILINE)
    fm_ver = m.group(1) if m else "<none>"
    if fm_ver != cfg["meta"]["version"]:
        fails.append(
            f"{tag} 版本不一致: frontmatter {fm_ver} != meta.version {cfg['meta']['version']}"
        )

    # 2) meta
    need(cfg["meta"]["brief_filename"], "meta.brief_filename")

    # 3) constraints
    c = cfg["constraints"]
    need(str(c["max_participants"]), "constraints.max_participants")
    need(str(c["duration_minutes"]), "constraints.duration_minutes")
    need(f"（{c['ask_options_per_question']}）", "constraints.ask_options_per_question")

    # 4) time_allocation：分钟 + 占比都必须在表里出现，且自身守恒
    minutes_sum = sum(s["minutes"] for s in cfg["time_allocation"])
    pct_sum = sum(s["pct"] for s in cfg["time_allocation"])
    if minutes_sum != c["duration_minutes"]:
        want = c["duration_minutes"]
        fails.append(
            f"{tag} time_allocation 分钟合计 {minutes_sum} != duration_minutes {want}"
        )
    if abs(pct_sum - 1.0) > 0.02:
        fails.append(f"{tag} time_allocation pct 合计 {pct_sum:.3f} 偏离 1.0")
    for slot in cfg["time_allocation"]:
        pct_txt = f"{slot['pct'] * 100:.1f}%"
        stem = slot["label"].split("（")[0]  # 「讨论（含 30 题 · 3 部分）」→「讨论」
        row = re.search(
            rf"^\|\s*{re.escape(stem)}[^|]*\|\s*{re.escape(pct_txt)}\s*\|\s*{slot['minutes']}\s*\|",
            md,
            re.MULTILINE,
        )
        if not row:
            fails.append(
                f"{tag} 附录 A.5 缺行或数值不符: {stem} / {pct_txt} / {slot['minutes']} min"
            )

    # 5) style
    st = cfg["style"]
    need(st["output_path_template"], "style.output_path_template")
    for g in st["pos_groups"]:
        need(g, "style.pos_groups")
    for v in st["phase_labels"].values():
        need(v, "style.phase_labels")

    # 6) vocab_targets
    for lv, (lo, hi) in cfg["vocab_targets"].items():
        if f"{lo}–{hi}" not in md:
            fails.append(
                f"{tag} vocab_targets[{lv}] = {lo}–{hi} 未出现在 {SKILL_MD_NAME}"
            )

    # 7) exam：等级标签
    for lv in cfg["exam"]["levels"]:
        need(f"({lv})", "exam.levels")

    # 8) question_plan：ask=false 的题不得被描述为「询问」
    for q in cfg["question_plan"]:
        row = re.search(rf"^\|\s*{q['id']}\s*\|([^\n]*)$", md, re.MULTILINE)
        if not row:
            fails.append(f"{tag} §3 交互契约表缺 {q['id']} 行")
            continue
        line = row.group(1)
        if q["ask"] is False and "不询问" not in line:
            fails.append(f"{tag} {q['id']} 配置 ask=false，但 §3 表未标注「不询问」")
        if q["ask"] is True and "不询问" in line:
            fails.append(f"{tag} {q['id']} 配置 ask=true，但 §3 表标注了「不询问」")

    # 9) 话题机制：题库 + 随机 + 自定义
    pool = cfg.get("topic_pool", [])
    if not pool:
        fails.append(f"{tag} topic_pool 为空，Q4 无题可选")
    else:
        if "topic_pool" not in md:
            fails.append(f"{tag} 配置了 topic_pool，但 {SKILL_MD_NAME} 未提及该键")
        if "题库" not in md:
            fails.append(
                f"{tag} 配置了 topic_pool，但 {SKILL_MD_NAME} 未出现「题库」说明"
            )
    for q in cfg["question_plan"]:
        if q.get("allow_random"):
            label = cfg["style"]["i18n"].get("topic_random_label", "随机")
            if label not in md:
                fails.append(
                    f"{tag} {q['id']} 开启 allow_random，但 {SKILL_MD_NAME} 未出现"
                    f"随机项文案 {label!r}"
                )
        if q.get("allow_custom") and "自定义" not in md:
            fails.append(
                f"{tag} {q['id']} 开启 allow_custom，但 {SKILL_MD_NAME} 未出现「自定义」说明"
            )

    # 10) 内容纯度：包内不得引用其它语言的配置文件名
    aliens: list[tuple[str, str]] = []
    for f in sorted(skill_root().rglob("*")):
        if not f.is_file() or f.suffix not in {".md", ".py", ".json"}:
            continue
        if ".rumdl_cache" in f.as_posix():
            continue
        text = f.read_text(encoding="utf-8")
        rel = f.relative_to(skill_root()).as_posix()
        for name in sorted(set(re.findall(r"[\w-]+-corner-config\.json", text))):
            if name != DEFAULT_CONFIG_NAME:
                aliens.append((rel, name))
    for rel, name in aliens:
        fails.append(f"{tag} {rel} 引用了其它语言的配置 {name!r}")

    return fails


def main() -> int:
    """三段闸门：schema（引用 + 必填顶层键）→ 身份 → 文档 ↔ 配置；任一失败即停。"""
    if not config_path().is_file():
        print(f"{SKILL_NAME} ({LANG}): 配置缺失")
        print(f"  ✗ 缺少 {config_path().as_posix()}")
        return 1
    cfg = json.loads(config_path().read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        print(f"{SKILL_NAME} ({LANG}): 1 处不一致")
        print(f"  ✗ 配置顶层必须是 JSON 对象，实际为 {type(cfg).__name__}")
        return 1
    fails: list[str] = []
    for stage in (audit_schema, audit_identity, audit):
        fails = stage(cfg)
        if fails:
            break
    print(
        f"{SKILL_NAME} ({LANG}): {'OK' if not fails else str(len(fails)) + ' 处不一致'}"
    )
    for line in fails:
        print("  ✗", line)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
