# skill 复核报告

**口径**：只比照 `docs/basics.md` 的硬规则；结论均可用仓库内命令复现，自称的数字要能复算。
行数与 token 按 **bytes ÷ 3.5** 估算，长句按**显示宽度**计（CJK 记 2 列），排除表格行、代码块与 frontmatter。
**本报告不改任何包** —— 改哪个由你逐个点名放行；条目修完即删，只承载未决项，编号不复用、跳号正常。

## 结果

### 合规：9 个包违规 0 条

`project-tex`、`skill-draft`、`project-py`、`project-typ`、`anchor-french`、`anchor-spanish`、`scoop-main-plus`、`scoop-extras-plus`、`scoop-extras-cn` 对照 25 条硬规则逐条对账后**违规 0 条**；四项全仓共性检查一律 **9/9**：

| 共性检查     | 现状                                                                                                                                                                                                                                              |
| :----------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 技能类型标注 | 每包一级标题下一行：类型 → 破折号 → 一句判定理由（约束面 / 工序面）                                                                                                                                                                               |
| 脚本化自检   | 每包一键可跑：`skill-draft` 用 `verify.py` + `checkers.py`；`project-py` / `project-typ` 用 `scripts/selfcheck.py`；`anchor-*` 用 `scripts/corner_audit.py`；`project-tex` 用 `check_style.py --selfcheck`；`scoop-*` 用 `scripts/sm_selftest.py` |
| 踩坑点节     | 单独成节、与检查清单并列，落在「流程讲完、参考材料之前」。唯一例外是 `scoop-extras-cn`：14 条整体外置到 `references/gotchas.md`，正文 §7 留路由句 + 标题索引                                                                                      |
| 正文超软门槛 | 5k token / 500 行。仅 `project-typ` 超线（351 行 / ~5.9k），已在文末 `## 篇幅说明` 写明理由；其余在线内                                                                                                                                           |

### 已验证，别改坏

- **`references/` 双向守卫有效**：9 个包的参考文件既无死文件也无悬空指针；`SKILL.md` 与 `references/*.md` 之间零重复段落（按 ≥60 字符的段落逐包比对）。
- **scoop 三包自检的组数声明与实际一致**：`SKILL.md` 写 7 / 7 / 8，实际打印 `[1]…[7]` / `[1]…[7]` / `[1]…[8]`。
- **`project-typ` 的自检会复算自己文末的篇幅数字**（写 351 行 / ~5.9k token，实测 5,932.9 token，偏差 < 5%）—— 全仓唯一一处「文档自称的数字必须能被复算」的机械守卫。
- **`corner_config.skill_root()` 用 `__file__` 定位、布局不对就抛错**，不静默降级；`SKILL_NAME` 这份「代码里的第二真源」由 `corner_audit.py` 强制与目录名、frontmatter 三方对齐。
- **`project-py` / `project-typ` 的 `selfcheck.py` 声明 `Report-only -- nothing is ever rewritten`**，并把退出码语义写进 docstring。
- **`project-tex/check_style.py` 的规则表双向核对**（脚本有表缺 → `missing`，表有脚本缺 → `extra`）。
- **`_read()` 里两个 `except` 子句刻意分写**，原因写在 docstring（PEP 758 下 `except (A, B):` 会被改写、只在 3.14+ 可解析）—— 踩坑点写进了代码，而不只是文档。
- **`anchor-*` 三个脚本共用一套退出码约定**：`0` 干净 / `1` 有 finding / `2` 用法错或自检自身跑不下去（包布局不对、配置或正文读不了）。`corner_skill.py` 的自检用 `_check()` 而非 `assert`，`python -O` 下照样会失败。
- **长句不再集中在 `anchor-*`**：四个文件从 21 / 22 / 26 / 26 行降到 0。手法是长枚举拆成可见列表、复合句只在 `。` / `；` / `、` 处断开，没有硬切句子。

## 建议

1 条未决，**待点名放行**：

| #   | 严重度 | 问题                                                                                                                                                                                                                                                        | 建议改法                                                                                | 落点                        |
| :-- | :----- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------- | :-------------------------- |
| R10 | P2     | `ruff format` 的射程含 `.md` 里带 `python` / `py` 标记的围栏（标 `text` 与不标语言的不碰），而 `file-types.json` 的 markdown 组只跑 `rumdl` —— 门口播报 `Gate passed` 不代表代码块格式化过了；按直觉手跑 `ruff format .` 还会改到两份文档，容易被当误改回滚 | 把 `ruff format --check` 加进 markdown 组的 verify，让「门禁过了 = 格式化也过了」成立   | 全仓 2 个 `references/*.md` |

另有一项本轮新发现、未编号：**`scoop-extras-cn` 的 `sm_selftest.py` 报 2 处失败** —— `references/porting.md` 被 `SKILL.md` 索引但文件已不在磁盘（包内 6 处引用悬空），以及 bucket 里 6 个 error-level manifest（`cajviewer`、`cnkiexpress`、`edrawmax8`、`feishu`、`mpv.net-cm`）。两者都与文档改动无关，其余八个包自检全绿。

最小复现：

```text
$ ruff format --check --no-cache .                 # -> 2 files would be reformatted
```
