# 高频 Typst 写法与排雷

## 文件形态

### 幻灯片 deck

```typst
#import "lib/lib.typ": *

#show: touying-quick.with(
  title: "环境搭建",
  info: info-cv,
  bgimg: bghexagon,
)

# 可选：把无关章节片段拉进来
#include "z-Python环境搭建.typ"

= OpenCV            // 一级标题 → 章节扉页（自动成页）
== 简介             // 二级标题 → 内容页（自动成页）
=== 中缀到后缀      // 三级标题 → 拆页
```

`= / ==` 各自自动成页，**不需要写 `#pagebreak()`**。
唯一需要显式拆页的情况是一个 `==` 装不下、要拆成多个 `===` 时。

### 章节片段

无任何文件头，首行直接是 `= 标题`。被 deck 用 `#include` 拉入，继承 deck 的样式。
`z-` 前缀的文件都是这种片段（`z-Python环境搭建.typ`、`z-个人介绍.typ`、`z-Python学习.typ`）。

## 控制单页容量

decks 里最常出问题的是**内容撑破 16:9 单页**。惯用手法：

```typst
// 分栏（columns() 默认两栏）—— 栏与栏之间必须显式 #colbreak()
#columns()[
  #set text(size: 16pt)
  左栏内容
  #colbreak()
  右栏内容
]

// 单栏限高
#block(height: 15em)[
  #set text(size: 18pt)
  ...
]
```

- 分栏块**不套 `block(height: …)`**：高度由内容决定，换栏靠 `#colbreak()`；
  `columns(n)` 就要 n−1 个 `#colbreak()`。
- **例外**：块里有有序列表（`+` / `1.`）时，保留 `#block(height: 18em, columns()[…])`，
  且块内**不写 `#colbreak()`** —— 分栏交给块高，两者混用断点会有两个来源。
  `#colbreak()` 还会截断有序列表、右栏编号从 `1.` 重来；靠块高隐式分栏则编号连续（见 SKILL.md §2.1）。
- 移除固定高度后每页不再预留那段空白，版面会变紧凑、分页点前移，页数可能变化 ——
  用 `code/deck_pages.py render` / `diff` 前后逐页比像素确认。
- 正文字号在块内**显式**`#set text(size: ...)`：常用 18pt（正文）、16–17pt（较密）、
  12–15pt（含代码）、10–11pt（长代码）。
- `columns()` 不带参数即两栏；栏宽按 `columns(n, gutter: g)` 现算，别拿两栏的宽度去量三栏块。

## 表格

```typst
// 1) 外部 CSV + 三线表（首选）
#let data = csv("data/algo-expr.csv")
#figure(
  tableq(data, 3),
  caption: "运算表达式",
)

// 2) 手写三线表
#figure(
  table(
    columns: 3,
    inset: 0.3em,
    align: center + horizon,
    stroke: table-three-line(rgb("000")),
    [触发键], [功能键], [作用],
    [中键], [], [旋转视图 Orbit],
  ),
  caption: none,
)

// 3) xlsx（仅多 sheet / 公式时）
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

`csv()` 返回「行数组」，每个元素是「列数组」，与 `tableq` 的 `data` 参数形状一致，
用 `..data.flatten()` 展开成 table 的位置参数。

## 代码块

````typst
// 外部文件（首选）
#code(read("blender/v04_blender_morphology.py"))

// 短片段直接写围栏
```python
img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
```
````

围栏代码块由 codly 接管，**自带行号**。局部关掉行号：

````typst
#no-codly[
```python
x = 1
```
]
````

deck 里出现 `raw` 块时，`code-block-style` 已经把它调成灰底圆角。

## 数学

```typst
$ y = w^T x + b $

$
  V(s) = max_a sum_(s') P(s' | s, a) (R(s, a, s') + gamma V(s'))
$ <bellman>

见 @bellman
```

- **CJK 进公式**用 `ctext("...")`：`(ctext("色泽")=? ) ∩ (ctext("根蒂")=? )`。
- 带 label 的公式自动获得 `(章节号.序号)` 编号。
- 多行/分段用 `cases`、`&` 对齐。

## 键位与提示框

```typst
#kbd("Ctrl")            // 来自 keyle

#note[一句话提示]
#warning[危险]
#caution[注意]
#tip[...]
#quote[...]
```

`note[...]` 常用于页面底部给一句总结，外面可再包一层字号设置：

```typst
#[
  #set text(size: 15pt)
  #note[
    一句话：`ops` 是「用户动作」，`data` 是「文件内容」，`context` 是「你此刻站在哪儿」。
  ]
]
```

## 图片

```typst
#figure(
  image("images/blender-ui.png", height: 50%),
  caption: none,
)
```

- 一律 `figure` 包 `image`，默认 `caption: none`。
- **`height` / `width` 只写百分数**，不写 `pt` / `em` / `cm` / `mm` / `in` / `auto`。
- 百分比相对**所在容器**解析：分栏块高度是 auto，基准变成页面（栏）内可用高度，
  数值要按新基准重新标定，别照抄旧百分比；想让图占满一栏就给 `width: N%`（见「控制单页容量」）。
- 需要并排两张图时用 `columns()` 或 `subpar` 的 `sgrid`。

---

## 排雷清单（踩过的坑）

### 1. 幽灵逗号

内容块 `[...]` 内的**可见逗号**会被解析成参数分隔符：

```typst
// ✗ 错
#note[第一句，第二句。],
// ✓ 对
#note[第一句，第二句。]
```

### 2. 双反引号 raw

`` `` ` `` `` 这种双反引号 raw 极易造成定界符错配，**吞掉后续整段文本和标题**。
需要展示反引号时用单反引号或纯文字描述。

### 3. raw 围栏必须配对

``` 与 ```` 嵌套要成对，否则级联破坏整个文件的解析。
在 Typst 里演示 Markdown 代码块时，内层用 `` ```text `` 而不是 `` ```markdown ``（避免 `**` 被染色）。

### 4. 超高 slide 被自动拆页

Touying 检测到内容超过一页会**自动拆成两页**，留下半页空白。
解法：精简内容、拆成多个 `===`，或者改成分栏版式（`columns()` + `#colbreak()`）。
**不要再靠 `block(height: …)` 把内容硬压进一页** —— 固定高度只是把溢出的部分藏起来。
（唯一的正当用法是分栏块里带有序列表，见「控制单页容量」。）

### 5. 路径基准是仓库根

`read()` / `image()` / `csv()` 的路径都相对**仓库根**，不相对当前 `.typ`。
deck 在根目录，所以看起来像相对路径；但如果把 `.typ` 移进子目录就会全部断链。

### 6. 编译必须带字体路径

```bash
typst compile --font-path "C:/Windows/Fonts" v01-环境搭建.typ
```

否则中文缺字（显示为空白或豆腐块）。`code/slide_qa.py` 已经把 `--font-path` 内置了。

### 7. 本机 shell 工具注意

- `find` / `grep` 是 scoop shim 版（BusyBox），行为与 GNU 不同：
  `grep` **不支持 `--include`**，`find -name` 报参数格式错误。
  → 搜文件/内容一律用编辑器的 Glob / Grep 工具。
- 不要用 shell `diff` 比对含中文的混合编码文件：遇到 GBK 字节会抛
  `UnicodeDecodeError` 并**静默返回 "(no diff)"**（假阴性）。
  → 用 Python `difflib` + 编码回退（`utf-8-sig` → `utf-8` → `gbk` → `latin-1`）。

### 8. 导出的 PNG 序列

`typst compile` 要导出多页图时必须带页码模板：

```bash
typst compile --font-path "C:/Windows/Fonts" --ppi 100 v05-几何变换.typ "output/{0p}.png"
```

缺 `{0p}` 会报 *cannot export multiple images without a page number template*。
