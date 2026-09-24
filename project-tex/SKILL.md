---
name: project-tex
description: LaTeX 数学公式的写法规范。写、改、审查公式时套用——覆盖行内与独立公式、多行推导、矩阵与行列式、方程组与分段函数、括号尺寸、转置/极限/argmin 记号、正体粗体斜体字体命令；落笔后用 scripts/check_style.py 复查。
---

# project-tex

**技能类型**：混合型 —— 规则表是硬约束（不写什么、改写成什么），「落笔」是四步工序。

公式按这套写法落笔，落笔后跑一次检查脚本。可整块照抄的样例在 [`references/examples.md`](references/examples.md)。

## 落笔

1. **选外层环境**：多行公式、矩阵、方程组都先按语义挑环境，不用没有语义的通用排版盒——见规则表的 `array` 行。
   完成标志：每个多行公式都能说出它为什么用这个环境。
2. **定括号与记号**：括号尺寸显式写出来；转置、极限箭头、argmin/argmax 取固定写法——见 `bigg`、`transpose`、`limit-arrow`、`underset-limits`、`underset-slots` 五行。
   完成标志：这五行对改过的文件零告警。
3. **定字体**：正体、粗体、斜体各只有一个合法命令——见 `mathrm`、`mathbf`、`mathit` 三行。
   完成标志：这三行对改过的文件零告警。
4. **复查**：`python <this skill dir>/scripts/check_style.py <改动过的文件>`。
   完成标志：退出码 0。有 finding 就按它的提示改，改完重跑，直到干净。

## 规则表

id 与脚本里的规则同名同义，两边改动要一起改。`--list-rules` 双向核对：既报「只进了脚本、没进本表」的 id，也报「只在本表、脚本里没有」的 id；两个方向都干净才退出 0。

| id | 不写 | 改写成 |
| --- | --- | --- |
| `array` | `\begin{array}` | 按语义换成 `gathered` / `gather` / `aligned` / `cases` / `vmatrix` / `bmatrix` |
| `bigg` | `\left...\right` | `\bigg...\bigg`，依内容在 `\big` / `\Big` / `\bigg` / `\Bigg` 里挑一档 |
| `underset-slots` | `\underset{w}` 这类只写一个参数位 | 两个参数位都写全：`\underset{w}{\mathrm{argmin}}`；空位留空花括号 `\underset{}{x}` |
| `transpose` | `^T` | `^{\top}` |
| `limit-arrow` | `\rightarrow` | `\to` |
| `underset-limits` | `\limits_` / `\limits^` | `\underset{}{}` / `\overset{}{}` |
| `mathrm` | `{\rm }`、`\mathop{}`、`\operatorname{}` | `\mathrm{}` |
| `mathbf` | `{\bf }` | `\mathbf{}` |
| `mathit` | `{\it }` | `\mathit{}` |

## 踩坑点

零 finding 不等于公式都对——先确认脚本有没有看见你的公式。发现一个加一个。

- **`.md` 报零告警，可公式确实违规。**
  现象：在 markdown 里改了公式，脚本干净退出。
  原因：`.md` 只查四个数学区（`$…$`、`$$…$$`、`\(…\)`、`\[…\]`）和语言标为 `latex` / `tex` / `math` / `katex` 的围栏块；裸写的公式、不标语言的围栏块，都不在检查范围内。
  对策：公式一律包进数学区，或给围栏块补上语言标注。
- **`.md` 与 `.tex` 的检查范围不同。**
  现象：同一段 `\begin{array}` 在 `.md` 里被放过，在 `.tex` 里被抓。
  原因：`.tex` / `.sty` / `.cls` 走全文件模式，只把 `%` 注释排除在外；`.md` 只查上面那几类区域。
  对策：按后缀判零告警的含义——`.tex` 零告警是真的干净，`.md` 零告警还得确认公式进了数学区。
- **行内 `$…$` 不跨行。**
  现象：跨了行的行内公式整段没被查。
  原因：行内分支的正则是「除 `$` 和换行外的任意字符」，碰到换行就匹配不上。
  对策：要跨行就改用 `$$…$$` 或围栏块。

## 扩展

加一条规则 = 在 `scripts/check_style.py` 的 `RULES` 里加一项，再在 `## 规则表` 里加同一 id 的一行。脚本只用标准库，改了直接跑就行。
