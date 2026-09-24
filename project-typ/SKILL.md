---
name: project-typ
description: 编写与修改Typst 课件时使用。规定代码/图片/数据三类外部文件的存放位置与引入方式，并要求在自定义函数前先检索 qooklet 与 touying-quick 的已有实现。触发词：Typst、typ、讲义、课件、幻灯片、touying、qooklet、.typ、figure、tableq、read()。
agent_created: true
---

# Typst 课件编写规则

所有仓库的 `.typ` 文件分两种形态，规则不同：

| 形态 | 特征 | 典型文件 |
| --- | --- | --- |
| **幻灯片** | 首行为 `#import "lib/lib.typ": *` + `#show: touying-quick.with(...)` | `v01-环境搭建.typ`、`m01-绪论.typ` |
| **章节片段** | 无文件头，直接用 `#include` 拉进来 | `z-Python环境搭建.typ` |

两者的资源规则完全一致：**一切外部内容都放在仓库根的对应目录里，用相对路径引入，绝不内联进 `.typ`。**

## 1. 六条硬规则

第 1 条管**动手前先查什么**；第 2–4 条管**资源怎么放、怎么引**；第 5 条管**文字怎么改**；第 6 条管**结果怎么汇报**。

### 1.1 自定义函数：先查包，再动手

**在写任何 `#let my-helper(...) = ...` 之前，必须先检索 qooklet 与 touying-quick 是否已经有实现。**
绝大多数排版需求（表格、代码块、提示框、公式编号、图表引用）这两个包都已经解决，重复造轮子会导致
版式不一致。

```bash
# 包的真实位置（Windows）
codes="$env:APPDATA/typst/packages"
# macOS 对应：~/Library/Application Support/typst/packages

ls "$env:APPDATA/typst/packages/local"      # 本地开发版（可改写、优先看这个）
ls "$env:APPDATA/typst/packages/preview"    # 已发布版
```

检索顺序：

1. **先看 `lib/lib.typ`** —— 仓库已经把常用能力通过 `#import "lib/lib.typ": *` 全部转发进来，
   绝大多数情况下直接用即可。
2. **查 `packages/local/<pkg>/` 的 `src/utils.typ` 与 `src/lib.typ`** —— 这里能看到全部导出符号。
3. **再查 `packages/preview/<pkg>/<version>/`** —— 版本更多，`preview` 下是各版本的完整快照。
4. 只有以上都没有，才自己写，并放到**仓库的 `lib/`** 里（而不是散落在章节文件中）。

已核实的常用符号（详见 `references/packages.md`）：

- **qooklet** → `tableq(data, k)`、`table-three-line(color)`、`table-no-left-right(color)`、`ctext()`
- **touying-quick** → `touying-quick.with(...)`、`bgsky`/`bghexagon`/`bgbook`/`bgyellowish`、`code()`、
  `ctext()`、`tip`/`note`/`quote`/`warning`/`caution`
- **theorion**（经 touying-quick 转发）→ 上述提示框本体，`set-theorion-numbering()`

> 注意 `code()`、`ctext()`、`tableq()` 在 qooklet 与 touying-quick 中**各有一份同名实现**，
> 课件里通过 `lib/lib.typ` 引入，deck 场景生效的是 touying-quick 版本，无需关心来源。
> 但 `ctext()` 更推荐直接写 `ctext("色泽")`（数学模式里用 CJK 的惯用写法）。

### 1.2 代码：存文件，用 `read()` 取回

写代码示例时，**不要把代码内联在 `.typ` 里**。先把代码落成真实文件，再用 `read()` 引入。

| 内容 | 存放目录 | 引入方式 |
| --- | --- | --- |
| 课件演示用的 Python 脚本 | `python/` | `read("python/xxx.py")` |
| 教材配套示例脚本 | `cv40examples/<主题>/` | `read("cv40examples/<主题>/xxx.py")` |
| Blender 脚本（bpy 合成数据） | `blender/` | `read("blender/xxx.py")` |
| 工具/维护脚本（非课件内容） | `code/` | 一般不在课件里展示 |

`python/` 与 `blender/` 的文件按 `vNN_主题.py` 命名（如 `v01_3_pixel.py`、`v04_blender_morphology.py`），
与对应章节号对齐。

`cv40examples/` 是教材配套示例，**只保留「主题目录一层」**（`cv40examples/<主题>/<文件>`，不再有更深的嵌套）；
这些脚本自身用相对路径 `../../images/…` 取图，依赖 `code/run_example.py` 的 `os.chdir(script.parent)`，
**从其它目录直接调用会找不到图**。新增示例脚本时按此层级放，不要再建节目录。

三种写法，按场合选：

```typst
// 最简：一行直接出代码块
#code(read("blender/v01_blender_object.py"))

// 常用：先绑定变量，便于一个页面复用或做字号控制
#[
  #set text(size: 12pt)
  #let codepy = read("python/v01_3_pixel.py")
  #code(codepy)
]

// 需要换语言高亮时显式指定（默认就是 python）
#code(read("blender/bpy_spiral.py"), lang: "python", width: 92%)
```

`code()` 由 touying-quick 提供（灰底、圆角、可断页），等价于 `block() + raw(block: true)`。

> ⚠️ **路径一律相对于仓库根**，不是相对于当前 `.typ` 文件。`v01-环境搭建.typ` 里写的是
> `read("blender/v01_blender_object.py")`，而不是 `../blender/...`。不要用 `@filename:line` 或绝对路径。

代码量较大时（超过约 20 行）改用两栏版式，左栏放代码、右栏放结果图，写法见 §2.1。

```typst
#columns()[
  #[
    #set text(size: 12pt)
    #code(read("python/v01_3_pixel.py"))
  ]
  #colbreak()

  #[
    #align(center + horizon)[
      #figure(image("images/v01-pixel-grid.png", width: 100%), caption: none)
    ]
  ]
]
```

### 1.3 图片：存 `images/`，`figure` 包 `image`

```typst
#figure(
  image("images/logo-opencv.png", height: 40%),
  caption: none,
)
```

- 图片一律放 `images/`，引用 `image("images/xxx.png", ...)`。
- **默认 `caption: none`** —— 课件图片通常不需要图注；确需图注时才写 `caption: "..."`。
- 高度用百分比（`40%` / `50%` / `80%` / `90%`），由所在容器决定基准；
  宽度可用 `width: 60%`。
- **不要单独写 `#image(...)`** —— 一律用 `#figure(...)` 包住，以保持版式与计数行为一致。
- 常用素材命名：`ai-*`、`bm-*`（生物医学）、`blender-*`、`app-cv-*`。新增前先确认 `images/` 里没有可复用的。
- `images/` 被 `.gitignore` 忽略（**不在 git 里，删了不可回滚**），且 **PNG 已用 oxipng 无损压过**。
  重新生成或新增大量 PNG 后可以再压一遍：`python code/oxipng_images.py --days 7`（干跑），
  加 `--apply` 落盘 —— 会先备份到 `.tmp/backup-images-oxipng/`，压完逐张比像素，省约 30% 且像素不变。
  `oxipng` 只吃 PNG/APNG，`bmp`/`jpg` 不在能力范围内（批量转格式会打断 `image()` 引用，别做）。

### 1.4 数据：存 `data/`，优先 CSV

```typst
#let data = csv("data/algo-expr.csv")
#figure(
  tableq(data, 3),
  caption: "运算表达式",
)
```

- 数据一律放 `data/`，**优先 CSV**。
- CSV **第一行是表头**，`csv()` 读回来即可直接喂给 `tableq(data, 列数)`。
- 需要表格编号/引用时用 `figure(tableq(...), caption: "标题", supplement: "Table", kind: table)`；
  课件里更常见的是 `figure(tableq(...), caption: "...")`。
- 手写表格（少量、无外部数据）直接 `table(columns: n, stroke: table-three-line(rgb("000")), ...)`。
- 只有确实需要多工作表或单元格公式时才用 `xlsx`，写法：

  ```typst
  #figure(
    xlsx-parser(
      read("data/ml-melon-hypo.xlsx", encoding: none),
      parse-table-style: false,
      parse-stroke: false,
      stroke: table-three-line(rgb("000")),
    ),
    caption: "",
  )
  ```

  注意 `encoding: none` 是必需的（否则二进制被当文本解码）。

> 仓库根有 `.gitignore`，`images/` 与 `output/` 不入库；数据文件在 `data/` 下正常纳入版本管理。

### 1.5 文字：不要切分长句

**不要把长句拆成短句。** 保持原有的句子结构与表达节奏，一个完整语义就是一个句子。

```typst
// ✗ 错：把一个长句切碎
本方法先对图像做高斯滤波。然后计算梯度。再抑制非极大值。最后双阈值连接边缘。

// ✓ 对：保持一个完整长句
本方法先对图像做高斯滤波，然后计算梯度并抑制非极大值，最后通过双阈值连接得到边缘。
```

- 存量的 `.typ` 与 `python/`、`blender/` 源码里的中文语句**一律保持原样**，不做「短句化」改写。
- 涉及代码时同理：只改代码本身需要的部分，不顺手重排注释与文档字符串的句读。
- 需要断句时用**逗号、顿号或分号**维持单句，而不是用句号拆成多句。

### 1.6 结果：编译后不要展示 PDF

**编译只是为了验证能否通过，不要用 `present_files` 把产出的 PDF 推给用户，也不要在回复里附图。**
用户在自己的 IDE / 阅读器里看稿，助手弹出 PDF 只会打断工作流。

- 编译产物写到临时路径即可（如 `output/` 或 `/tmp/`），不必留在仓库根。
- 汇报时**只给结论**：编译是否通过、报错在第几行、`slide_qa.py` 报了哪些页。
- 需要用户确认版式时，描述清楚问题所在（页码 + 现象），让用户自己打开看，而不是把文件塞过去。
- 同理，`typst compile` 导出的 PNG 序列也只作为 `slide_qa.py` 的中间产物，不单独展示。

## 2. deck 骨架（照抄）

```typst
#import "lib/lib.typ": *

#show: touying-quick.with(
  title: "章节标题",
  info: info-cv,          // 见 lib/info.toml，决定页脚/作者/系列名/语言
  bgimg: bghexagon,           // bgsky | bghexagon | bgbook | bgyellowish
)

== 教学目标 <touying:hidden>

= 一级标题（自动成章节扉页）
== 二级标题（自动成内容页）
=== 三级标题（拆页）
```

- `info` 由 `lib/info.toml` 提供，已定义：`info-intro`、`info-cv`、`info-ml`、`info-biomed`、
  `info-algo`、`info-extra`、`info-extrax`、`info-philos`、`info-shakesp`、`info-public`、`info-dialog`。
- **一句式的教学提示用 `note[...]`**，危险/易错点用 `warning[...]` / `caution[...]`。
- 分栏页用 `#columns()[...]`，**栏与栏之间必须加 `#colbreak()`**，见下节。

### 2.1 分栏块：裸 `columns()` + `#colbreak()`，不套 `block(height:)`、不用 `grid`

分栏块统一写成这样（2026-09-24 起；旧的 `#block(height: 18em, columns()[…])` 由下面的脚本全数摘掉外层）：

```typst
#columns()[
  #[
    #set text(size: 12pt)
    #set par(leading: 0.62em)
    #code(read("cv40examples/06_object_counting/ex6.7_threshold_binary.py"))
  ]
  #colbreak()

  #[
    #align(center + horizon)[
      #figure(image("images/v03-ex6.7-threshold-binary.png", width: 100%), caption: none)
    ]
  ]
]
```

四条要点，都是踩过坑换来的：

1. **不要套 `#block(height: …)`，也不要用 `#grid(columns: (a, b), column-gutter: …)`。**
   高度交给内容自己决定；`columns()` 两侧等宽、没有列宽比参数，`grid` 只作真正需要表格语义时使用。
   （`#block(height: …)` 仍可给**单栏**内容限高，见 `references/syntax.md`。）
2. **每栏之间必须写 `#colbreak()`。** 高度变成 auto 之后 `columns()` 是**流式分栏**：
   不写 `#colbreak()` 就**根本不会流向下一栏**，后续内容会全部堆在第一栏里（静默改版面）。
   用默认的弱分栏（`#colbreak()` 而非 `#colbreak(weak: false)`）：前一栏恰好满栏时不会多切出一个空栏。
   **多栏块要写 n−1 个**——`columns(3)` 两个、`columns(4)` 三个，改写时按栏数逐个补。
3. **每栏用 `#[ … ]` 包住。** `columns()` 只接受**一个**内容块（写 `columns()[a][b]` 是语法错误），
   且块内 `#set` 会一直向后生效；包一层才能让左栏的字号 / 行距不串到右栏。
4. **块内的 `height: N%` 要改成绝对 `pt`。** 原基准是块高 H，摘掉外壳后百分比改按**页面剩余高度**解析，
   `image(…, height: 95%)` 会直接变形；按 `H × N%` 冻结（1em = 20pt，如 11em 块里的 90% → `198pt`）。

改写与校验的工具都在 `code/`：

```bash
python code/measure_columns_split.py                      # 实测各块的分栏点 -> .tmp/columns-split.json
python code/unwrap_columns_block.py --splits .tmp/columns-split.json            # 干跑
python code/unwrap_columns_block.py --splits .tmp/columns-split.json --apply    # 落盘
```

- 不给 `--splits` 时，**没有 `#colbreak()` 的块一律跳过**：固定高度是它唯一的分栏依据，
  摘掉外壳会整块塌进第一栏，比不改更糟。
- 分栏点不是猜的：按「可分页单元」切分正文（空行分段、段落若为列表再按同级列表项拆细），
  量每个前缀在**该块自己的单栏宽**下的自然高度，取第一个装不下的单元。
- **去掉固定高度不是纯格式化**：每页不再预留那段空白，版面会变紧凑、分页点整体前移，页数可能变化。
  用 `python code/deck_pages.py render .tmp/pages-base` 与 `render` + `diff` 逐页比像素确认有没有改坏。

## 3. 编译与校验

```bash
# 编译（Windows 必须带字体路径，否则中文缺字）
typst compile --font-path "C:/Windows/Fonts" v01-环境搭建.typ

# 渲染 + 版式体检（页脚侵入、空白残页、固定高度块超容）
python code/slide_qa.py v05-几何变换.typ
python code/slide_qa.py --all

# 示例页专检：单页版式（左代码 + 右结果图）的左栏代码是否超出分栏区（Typst 实测行高）
python code/check_example_fit.py
python code/check_example_fit.py --margin 60      # 只列余量 < 60pt 的

# 资源引用完整性（image/read/csv/include 是否有断链）
python code/asset_check.py
```

## 4. 格式化：typstyle

**改完 `.typ` 要跑 typstyle。** 命令：`typstyle --check .`（只读）、`typstyle --diff <f>`（只读预览）、
`typstyle -i <f>`（落盘）。

### CRLF 文件必须还原换行（**最容易踩的坑**）

typstyle **无条件把 CRLF 转成 LF**。本仓库有 11 个 CRLF 文件 —— `lib/lib.typ`、`u-en-intro.typ`、
`v00-课程设计.typ`、`v02-色彩与像素.typ`、`v03-阈值处理.typ`、`v04-形态学处理.typ`、
`v11-相机标定与三维重建.typ`、`v15-目标检测实战.typ`、`a05-计算机视觉.typ`、
`m14-强化学习.typ`、`z-个人介绍.typ`，可直接格式化会产生**整文件 diff**。

```python
# 格式化后把 CRLF 文件的换行还原
p.write_text(p.read_text(encoding="utf-8"), encoding="utf-8", newline="\r\n")
```

> ⚠️ 还原 CRLF 后，`typstyle --check .` 会**一直报这 11 个文件待格式化** —— 这是换行差异，不是内容未格式化。
> 判断「内容是否已格式化」的正确做法：读成文本、以 `newline="\n"` 写临时文件再 `--check`，
> 返回 0 即已格式化。

其他要点：

- 默认会**按字母重排 import 项目**；需保持原顺序时加 `--no-reorder-import-items`。
- 格式化是**渲染中性**的：本仓库 54 个可编译文件格式化前后渲染 PDF 内容逐字节一致。
- 校验渲染是否被改动时，**比对 PDF 必须先剔除** `/CreationDate`、`/ModDate`、`D:...` 日期字面量、
  `<xmp:*Date>`、以及 `xmpMM:InstanceID` / `DocumentID`（Typst 每次构建随机生成），
  否则会误报差异。

## 5. 检查清单

生成或修改 `.typ` 后逐条核对：

- [ ] 代码没有内联，全部落在 `python/` 或 `blender/`，用 `read("...")` 引入
- [ ] 所有 `read()` / `image()` / `csv()` 路径都是**相对仓库根**的，且文件真实存在
- [ ] 新增函数前已检索 qooklet / touying-quick；重复实现的已删除，改用包的版本
- [ ] 图片放在 `images/`，用 `figure(image(...), caption: none)` 包裹
- [ ] 数据放在 `data/`，是 CSV；表格用 `tableq(data, 列数)`
- [ ] 中文长句保持完整，未被切分成短句
- [ ] 分栏块用裸 `columns()`（不套 `block(height:)`），**每栏之间都有 `#colbreak()`**（n 栏块有 n−1 个），每栏用 `#[ … ]` 包住
- [ ] 分栏块里的 `height: N%` 都已按原块高冻结成绝对 `pt`
- [ ] 已跑 typstyle；若文件原本是 CRLF，**换行已还原**
- [ ] 用 `--font-path "C:/Windows/Fonts"` 编译通过，且 `code/slide_qa.py` 无超容告警
- [ ] **没有**用 `present_files` 展示编译产出的 PDF / PNG

## 6. 参考文件

- `references/packages.md` —— qooklet / touying-quick / theorion 的完整导出符号与配置项
- `references/syntax.md` —— 高频 Typst 写法与排雷清单
