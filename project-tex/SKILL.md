---
name: project-tex
description: LaTeX 数学公式的写法规范。写、改、审查公式时套用——覆盖行内与独立公式、多行推导、矩阵与行列式、方程组与分段函数、括号尺寸、转置/极限/argmin 记号、正体粗体斜体字体命令；落笔后用 scripts/check_style.py 复查。
---

# project-tex

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

id 与脚本里的规则同名同义，两边改动要一起改；`--list-rules` 会报出只进了脚本、没进本表的 id。

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

## 扩展

加一条规则 = 在 `scripts/check_style.py` 的 `RULES` 里加一项，再在 `## 规则表` 里加同一 id 的一行。脚本只用标准库，改了直接跑就行。
