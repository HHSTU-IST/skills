# skills

[English](README.md)

一组 我的日常 Agent Skill 的集合。

每个 skill 都是一个自包含的包：一份由模型按需加载的 `SKILL.md`，外加 `scripts/`（确定性的代码）、`references/`（长文档，按需读取）和 `assets/`（模板与数据，永不进入上下文）。skill 的 frontmatter 里 `name` 必须等于其目录名，否则不会被加载。

本仓库是主要工作副本。一个 skill 只要落在 WorkBuddy 会扫描的 skills 目录里，就对应用可用，而两个候选位置的作用范围不同：

| 层级 | 路径 | 可用范围 |
| :--- | :--- | :--- |
| 用户级 | `~/.workbuddy/skills/<name>/` | 本机所有项目 |
| 项目级 | `<project>/.workbuddy/skills/<name>/` | 仅该项目，且随项目一起分享给他人 |

skill 的目录名必须与 frontmatter 里的 `name` 一致，否则不会被加载。

## 安装 skill

### 1. 把包放到应用会扫描的位置

最简做法是复制——WorkBuddy 在每次启动时扫描目录树，因此单纯复制即可生效，无需其他步骤：

```bash
cp -r <skill> ~/.workbuddy/skills/<skill>            # 用户级，所有项目可用
cp -r <skill> <project>/.workbuddy/skills/<skill>    # 项目级，仅该仓库可用
```

若想只保留一份可编辑的副本，用链接指向它而不是复制：

```powershell
# Windows：目录 junction 不需要管理员权限
New-Item -ItemType Junction -Path "$env:USERPROFILE\.workbuddy\skills\<skill>" -Target "<repo>\<skill>"
```

```bash
# macOS / Linux
ln -s "<repo>/<skill>" ~/.workbuddy/skills/<skill>
```

### 2. 确认已加载

重启或重新加载 WorkBuddy，然后问它有哪些 skill 可用；或者直接检查目录是否存在、其 `SKILL.md` 能否解析。frontmatter 必须以第一行的 `---` 开头，`name` 必须是小写 kebab-case 且等于文件夹名；两者不一致是 skill 不显示的最常见原因。

注意复制体不会自动更新：改完包之后必须重新复制，或者改用链接，让编辑就地生效。

### 3. 从市场安装

发布到市场的 skill 通过 WorkBuddy 界面安装，而不是手工放置。本仓库并未发布，所以这里适用的是上面那条手工路径。

### 4. 用之前先验证

安装后跑一下包自带的自检。本仓库的每个 skill 都能离线自检：

```bash
python <installed skill>/scripts/sm_selftest.py    # Scoop 系 skill
python <installed skill>/scripts/verify.py .       # skill-draft
```

## 目录

| 分组         | Skill                                     | 一句话                                |
| :----------- | :---------------------------------------- | :------------------------------------ |
| 工具         | [`skill-draft`](#skill-draft)             | 构建 skill 包，并为其中每个文件设门禁 |
| 项目规范     | [`project-py`](#project-py)               | Python：包管理器、代码风格、ruff + ty |
| 项目规范     | [`project-typ`](#project-typ)             | Typst 课件：资源、版式、编译          |
| Scoop bucket | [`scoop-main-plus`](#scoop-main-plus)     | Main-Plus bucket 的 manifest          |
| Scoop bucket | [`scoop-extras-plus`](#scoop-extras-plus) | Extras-Plus bucket 的 manifest        |
| Scoop bucket | [`scoop-extras-cn`](#scoop-extras-cn)     | Extras-CN bucket 的 manifest          |

## 工具

### skill-draft

把一套工作流或一块领域知识变成一个 Skill 包，并让其中每个文件在**落盘之前**通过质量门禁。

铁律是：门禁不通过，文件就不算完成；每次写入之后立刻重跑门禁。一条命令驱动全部：

```bash
python <this skill dir>/scripts/verify.py <file-or-dir>...
```

每种文件类型都走三段流水线——内建检查、修复、复核——且复核段必须退出零。当前覆盖：

| 类型                       | 工具                          |
| :------------------------- | :---------------------------- |
| `.py`                      | ruff + ty，外加进程内语法编译 |
| `.md`                      | rumdl                         |
| `.json` / `.jsonc`         | 解析校验                      |
| `.ts` / `.js` 系           | oxlint + oxfmt                |
| `.css` / `.scss` / `.less` | oxfmt                         |
| `.png`                     | oxipng + chunk/CRC 完整性复核 |

新增一种文件类型通常只需编辑 `scripts/file-types.json`，不必改代码；进程内检查放进 `scripts/checkers.py`。本包只依赖 Python 标准库，别无其他，因此在任何机器上都能跑。

`SKILL.md` 里还有一节很长的"门禁细节"，记录了那些真花过调试时间的坑——`oxlint` 为什么需要 `--deny-warnings`、`oxipng` 的退出码为什么不可信、以及 `.jsonc` 这个后缀有时是刻意为之而不是笔误。

## 项目规范

这两个 skill 为另一个独立仓库（lectures）编码内部约定。它们是被动的：只描述规范，不运行任何东西。

### project-py

编写 `.py` 源码的规则。Notebook **明确不在范围内**。

- **包管理器是硬门禁。** 禁止 `pip install`。依赖变动只能经 `micromamba` 或 `uv`，且先与用户确认选哪个——选 `micromamba` 时，具体环境名要先问清楚才动手。
- **代码风格。** 迭代用 `enumerate()` / `zip()`，不用 `range(len())`；Matplotlib 走面向对象接口并配 `constrained_layout=True`；装饰通过 `ax.set(...)` 批量写，spines 一次传列表。
- **静态检查顺序固定：format → check → ty。** 格式化不是可选项，因为 `ruff check` 通过完全不代表格式正确。`ty` 必须指向真正装了依赖的解释器，否则会刷出一大片 `unresolved-import` 假警报。
- **文档、脚本、配置里都不许出现绝对路径，也不许写死版本号**——包括 `ty.toml`。两者都在运行时现取，因为写死的路径在机器一变化后就变成错误信息。

`references/toolchain.md` 收录了命令速查与隔离相关的注意事项。

### project-typ

编写和修改 Typst 课件的规则。

- **写自定义函数前先查包。** 在定义任何自定义函数之前，先在 `qooklet`、`touying-quick` 和 `theorion` 里搜一遍是否已有实现——绝大多数排版需求（表格、代码块、提示框、公式编号、图表引用）都已经解决，重复造轮子会导致版式不一致。
- **一切外部内容都放在文件里，绝不内联。** 代码放 `python/`、`blender/` 或 `cv40examples/`，用 `read()` 取回；图片放 `images/`，用 `figure(image(...), caption: none)` 包住；数据放 `data/`，优先 CSV，喂给 `tableq(data, k)`。路径一律相对于仓库根。
- **版式。** 固定高度的两栏块用 `columns()`，两栏之间必须有显式的 `#colbreak()`，每栏用 `#[ … ]` 包住——漏掉 `#colbreak()` 会**静默**改掉版面，因为 `columns()` 是流式分栏而非显式定位。
- **不要切分长句。** 中文长句保持完整；断句用逗号和分号，不用句号。
- **不要展示 PDF。** 编译只用于验证。汇报结论即可——是否编译通过、报错在第几行、`slide_qa.py` 报了哪些页——而不是把 PDF 推给用户的编辑器。

`references/packages.md` 记录三个包的导出符号；`references/syntax.md` 收集高频 Typst 写法与排雷清单。

## Scoop bucket

三个同构的 skill，把「上游发了新东西」或「上游发了新版本」变成一条命令。它们共享同一套架构：recipe catalog、共享库、三命令 CLI、自检，以及一个在写入之前校验结果的规则引擎。

它们只在各自目标仓库逼出来的地方不同。两个 extras 是把同一个 skill 移植到两个 bucket，README 约定不同、主导包型也不同；`scoop-extras-cn` 还在自己的 `SKILL.md` 里记录它与 `scoop-extras-plus` 的差异。

|             | `scoop-main-plus`          | `scoop-extras-plus`          | `scoop-extras-cn`          |
| :---------- | :------------------------- | :--------------------------- | :------------------------- |
| 目标 bucket | `$Scoop/buckets/main-plus` | `$Scoop/buckets/extras-plus` | `$Scoop/buckets/extras-cn` |
| recipe 数   | 18                         | 16                           | 16                         |
| lint 规则数 | 22                         | 22                           | 22                         |
| README 语言 | 英文                       | 英文                         | 中文                       |

**共同形态。** 三者暴露同样的三个触发命令：

| 命令       | 别名    | 职责                                |
| :--------- | :------ | :---------------------------------- |
| `generate` | `gen`   | 从 recipe 生成 manifest 骨架并填好  |
| `update`   | `upd`   | 改字段、升版本、重算 hash、探测上游 |
| `lint`     | `check` | 跑规则目录并修复格式                |

除 `--checkver`、`--fetch-hash` 和 `--rehash` 之外，一切都在离线状态下运行。只依赖 Python 标准库，因此任何 Python 3.11+ 都可以。脚本自行推导包根，可从任意工作目录运行。

### 共同保证

- **bucket 根在运行时解析**，绝不写死。解析顺序为 `--repo <path>`，其次从当前目录向上查找，最后是该 bucket 在 `$Scoop` 下已安装的那一份。任何包里都不存展开后的 Scoop 路径，一旦字面量重新出现，自检就会失败。
- **规则引擎在写入之前运行。** error 级发现会阻断写入；`--force` 可覆盖。`--dry-run` 预览，`--print-json` 转储结果。
- **保留既有键序。** `update` 只把**新**字段放进它们的规范位置；整体重排需要显式传 `--reorder`。
- **hash 绝不臆造。** 要么 `--fetch-hash` 流式下载并计算，要么 `--hash-from-file` 用磁盘上已有的包，要么该次运行打印提示、让你随后跑 `bin/checkhashes.ps1`。
- **README 是受控的。** 同步只触碰它认得出来的 summary 表，其他每一列保持逐字节不变。若章节缺失，则跳过同步并给出说明，而不是把文件改坏。
- **不支持 32bit。** `arch` 只接受 `64bit` 和 `arm64`，因此 `url32` / `hash32` 既不接受也不产出。

写入目标永远是 `<repo>/bucket/<app>.json` 加上 README 行；`bin/`、`scripts/` 和 `.github/` 归属 Scoop 与各仓库的 CI，永不触碰。

### scoop-main-plus

**Main-Plus** bucket 的 manifest。该 bucket 是 bin-first 的：40 个包里有 39 个通过 `bin` 安装，且完全没声明 `shortcuts`。出现 shortcut 才是例外，意味着这个包其实不是 CLI 工具。不给 `--repo` 时，从任意工作目录都会解析到 `$Scoop/buckets/main-plus`。

`generate` 会先敲定六个问题——上游、发布物形态、版本号、什么进 PATH、是否真的需要 shortcut、以及写进 README 的实现语言——并且**问**而不是猜。该 bucket 产出规范键序，用 `--flat-url` 把单架构的 `architecture` 块压缩掉，并把 18 个 recipe 各自的总体依据记录在 `references/coverage.md`。

### scoop-extras-plus

**Extras-Plus** bucket（56 个 manifest，面向英文）的 manifest。16 个 recipe；README 用一张 `## ⭐️ Summary` 表横跨五个 `###` 章节，三列为 `App / Auto-Update ? / Note`。

基线：整个 bucket **0 条 error 级发现**。`lint` 打印实时计数而不是一个冻结的数字，因为 bucket 会随每次 autoupdate 提交而增长。`SKILL.md` 列出了至今发现的真实问题，每条都标出抓到它的规则——URL 里写死的版本已与 `version` 不匹配、Scoop 不接受的 `md5:` hash 前缀、以及几处与 manifest 名漂移的 README 拼写。

### scoop-extras-cn

**Extras-CN** bucket（88 个 manifest，面向中文）的 manifest。与 Extras-Plus 版本共用同一份 recipe catalog、同一批 builder、同一套规范键序；差异都是这个 bucket 实际逼出来的，`SKILL.md` 把它们全部列成表。

它的独特性在于：

- **双语 description。** 88 个 manifest 里有 57 个用中文，因此强制英文措辞的规则对所有含 CJK 的字符串让位——句末句号检查也一并让位，因为中文句子合法地以 `。` 结尾。
- **四列 README**（`中文名称` 在 `App` 之前），CJK 单元格按显示宽度对齐，分在 `跨平台` / `Win 专属` / `开源镜像` 之下，另有一张两列的纯文本镜像表。
- **一条在别处是死代码的规则。** README 检查原本卡死在英文标题 `## ⭐️ Summary` 上，而本仓库写的是 `## ⭐️ 总结`，所以它从未触发过。改按「README 有 summary 表」判定后，它一次冒出 35 条发现，干净地分成 17 条稳定约定的条目和 18 条真实的 README 缺口——这很好地说明了为什么一个谁都过不了的检查比没有检查更糟。

有两处上游规则修复被带进了这个版本，因为它们是潜在 bug 而非仓库特定的选择：`jsonpath` / `xpath` 的正则要求，以及一个过度转义、永远匹配不上的递归删除模式。

## 维护一个 skill

每个 skill 都能离线自检：

```bash
python scripts/sm_selftest.py            # Scoop 系 skill：完整自检
python scripts/verify.py .               # skill-draft：为每个文件设门禁
```

自检不是摆设。它们双向强制 recipe ↔ builder 的覆盖、docs ↔ code 的一致性（lint 规则表必须与代码逐字一致）、针对真实 bucket 的往返序列化、README 同步的幂等性，以及 skill 的 `name` 等于其目录名这一条规则。

### 动手编辑前值得知道的两条约定

**绝不向 scoop skill 添加 `.json` 数据文件。** bucket CI 会把仓库里每一个*变更过的* `.json` 拿去对照 Scoop 的 manifest schema 校验——而且是**全仓范围**，因为那份变更文件清单会忽略自己的路径过滤器。skill 里放一个非 manifest 的 `.json` 就会让 CI 变红。这就是 recipe catalog 以 `assets/recipes.jsonc` 形式发布的原因：`.jsonc` 这个后缀是刻意的规避手段，其内容保持严格 JSON，而不是使用注释。

**绝不把机器本地的绝对路径写进 skill。** 包会被复制和移植，写死的路径在复制的那一刻就变成错的。指代 skill 自身请用 `<this skill dir>` 占位符，指代家目录请用 `~`，工具与环境的位置一律运行时解析。`skill-draft` 的 `no-local-paths` 检查为此兜底。
