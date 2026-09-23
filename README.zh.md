# skills

[English](README.md)

一组 我的日常 Agent Skill 的集合。

每个 skill 都是一个自包含的包：一份由模型按需加载的 `SKILL.md`，外加 `scripts/`（确定性的代码）、`references/`（长文档，按需读取）和 `assets/`（模板与数据，永不进入上下文）。skill 的 frontmatter 里 `name` 必须等于其目录名，否则不会被加载。

本仓库是主要工作副本。一个 skill 只要落在 WorkBuddy 会扫描的 skills 目录里，就对应用可用，而两个候选位置的作用范围不同：

| 层级   | 路径                                  | 可用范围                         |
| :----- | :------------------------------------ | :------------------------------- |
| 用户级 | `~/.workbuddy/skills/<name>/`         | 本机所有项目                     |
| 项目级 | `<project>/.workbuddy/skills/<name>/` | 仅该项目，且随项目一起分享给他人 |

skill 的目录名必须与 frontmatter 里的 `name` 一致，否则不会被加载。

## 安装 skill

### 把包放到应用会扫描的位置

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

### 用 npx 安装

若目标 skill 已存在于公开的 Git 仓库或市场，`skills` CLI 可以一步完成抓取与放置，无需手工复制：

```bash
npx skills find "关键词"                          # 交互式搜索
npx skills add <owner>/<repo> -g -y              # 装仓库内全部 skill，用户级
npx skills add <owner>/<repo>@<skill-name> -g -y # 只装指定的一个
npx skills add <owner>/<repo> -y                 # 项目级（默认行为）
npx skills list                                  # 查看已安装
npx skills update                                # 更新到后续版本
npx skills remove <skill>                        # 卸载
```

值得记住的参数：`-g` / `--global` 装到 `~/.workbuddy/skills/` 而不是项目内，`-y` / `--yes` 跳过确认，`-s` / `--skill` 按名字挑选，`-a` / `--agent` 指定目标 agent，`--copy` 在默认会建符号链接时改为复制文件，`--list`（`-l`）只列出仓库提供哪些 skill 而不安装。组合写法：`npx skills add <owner>/<repo> --all` 等价于 `--skill '*' --agent '*' -y`。

这条路有两个限制。它需要能访问 GitHub——在防火墙后会在 `Cloning repository…` 处卡住并最终在 443 端口失败，这属于代理问题而非 skill 问题；而且它只能安装上游确实存在于 GitHub 或市场的包。本仓库的 skill 并未发布到那些地方，所以对本仓库而言适用的仍是上面的复制或链接路径；这里真正有用的是 `npx skills init <name>`，它可以生成一个骨架包供你填充。

### 从市场安装

发布到市场的 skill 通过 WorkBuddy 界面安装，或按上面的 `npx skills add` 安装，而不是手工放置。本仓库并未发布，所以对它适用的是手工路径。

### 用之前先验证

安装后跑一下包自带的自检。本仓库的每个 skill 都能离线自检：

```bash
python <installed skill>/scripts/sm_selftest.py    # Scoop 系 skill
python <installed skill>/scripts/verify.py .       # skill-draft
python <installed skill>/scripts/check_style.py --list-rules  # project-tex
```

## 调用 skill

这些 skill 都不需要显式命令来触发。六个都没有声明 `disable-model-invocation`，因此 WorkBuddy 是拿你的措辞去匹配 `description` 及其触发词，从而决定加载哪一个。由此推出两件事：**用 skill 已经列出的词汇来表述需求**，是让它被加载的关键；而当一句话可能落在多个 skill 上时，**直接点名**才是强制指定它的手段。

下面的例子都用各 skill 自己的触发词。凡是封装了 CLI 的 skill，也会给出它将要构造的调用形式——很多时候，知道一个精确调用的形状比知道触发词更有用。

### skill-draft

触发词：*create a skill、new skill、write SKILL.md、save this workflow as a skill、edit a skill、validate a skill package、add a file type to the gate。*

```text
把我刚才做的事整理成一个 skill。
```

```text
建一个"旋转 PDF 页面"的 skill，然后对它跑一遍门禁。
```

```text
把 .toml 加进门禁的规则表，用 taplo。
```

第三条是扩展路径：新增一种文件类型通常只需编辑 `scripts/file-types.json` 一处，不必改代码，而这个 skill 知道这一点。

### project-py

触发词：*Python、py、ruff、ty、lint、类型检查、包管理、micromamba、uv、matplotlib、subplots。*

```text
给这些图加上误差棒，顺便把绘图代码收拾干净。
```

```text
下一节要用 scipy，装一下。
```

```text
对 python/ 目录跑一遍 lint 和类型检查。
```

第二条值得单独说明：这个 skill 在问清楚你要 `micromamba` 还是 `uv`、以及具体环境名之前，不会安装任何东西——`pip install` 会被直接拒绝。

### project-tex

触发词：*LaTeX、latex、tex、公式、数学公式、矩阵、行列式、方程组、分段函数、begin、aligned、bmatrix、vmatrix、mathrm、atop。*

```text
把这段推导整理成多行公式，按语义挑环境。
```

```text
写一下这个分段函数，再配一个矩阵。
```

```text
这段公式检查一下写法。
```

第三条是它的机械那一半：会执行 `python <this skill dir>/scripts/check_style.py <文件>`，该脚本只报告不改写，干净时退出码为 0。它既认 Markdown 也认 `.tex`——能从 `$…$`、`$$…$$`、`\(…\)`、`\[…\]` 以及 `latex` 围栏代码块里取出公式，所以讲义笔记和源文件受到的审查是同一套。

### project-typ

触发词：*Typst、typ、讲义、课件、幻灯片、touying、qooklet、.typ、figure、tableq、read()。*

```text
给图像处理那份课件加一节直方图均衡化。
```

```text
这一页溢出了，检查一下版式并修好。
```

```text
把这段代码做成两栏幻灯片，右边配输出图。
```

这里最要紧的两条提示正好对应两条规则：任何"新定义一个 helper"的请求都应该先走一遍查包；第三个例子必须落成一个 `python/` 下的真实文件、通过 `read()` 引入，绝不能内联进 `.typ`。

### scoop-main-plus

触发词：*generate manifest、new manifest、update manifest、lint manifest、scoop-main-plus、main-plus、scoop manifest、bucket manifest、checkver、autoupdate、hash verification、version bump、Excavator。*

```text
给 main-plus 加上新版 ripgrep 的 manifest。
```

```text
把 main-plus 里所有包都升一遍版本并重算 hash。
```

```text
检查一下 main-plus bucket。
```

底层对应的是 `gen --name <app> --recipe <recipe>`、`upd --all --checkver --apply --rehash` 和 `lint`；不传 `--repo` 时 bucket 从 `$Scoop` 解析。

### scoop-extras-plus

触发词：与 main-plus 同一组，把 *main-plus* 换成 *scoop-extras-plus*。

```text
给新版 IsoBuster 加一个 manifest。
```

```text
extras-plus 里哪些包的版本和 URL 已经对不上了？
```

```text
把我刚加的那几个包同步进 README 总结表。
```

第二条是 lint 规则能直接回答的只读问题（`W104`），比跑一次版本升格审计更省事。

### scoop-extras-cn

触发词：与上面同一组，再加 *scoop-extras-cn* 以及中文形式 *生成 manifest、更新 manifest、检查 manifest。*

```text
给 extras-cn 加一个新包，中文名是「飞书」。
```

```text
检查一下 extras-cn 的 README 总结表，哪些包没列进去？
```

```text
把 extras-cn 里所有包检查一遍，并把格式问题修掉。
```

第一条会用到这个 bucket 独有的四列 README 与 `中文名称` 单元格；第二条会命中 `W105`，它的提示会报出实际找到的拼写，这正是让"展示名与 manifest 名不一致"这类问题无需手工翻 README 就能定位的原因。

## 目录

| 分组         | Skill                                     | 一句话                                |
| :----------- | :---------------------------------------- | :------------------------------------ |
| 工具         | [`skill-draft`](#skill-draft)             | 构建 skill 包，并为其中每个文件设门禁 |
| 项目规范     | [`project-py`](#project-py)               | Python：包管理器、代码风格、ruff + ty |
| 项目规范     | [`project-tex`](#project-tex)             | LaTeX 数学公式：环境、括号、记号      |
| 项目规范     | [`project-typ`](#project-typ)             | Typst 课件：资源、版式、编译          |
| Scoop bucket | [`scoop-main-plus`](#scoop-main-plus)     | Main-Plus bucket 的 manifest          |
| Scoop bucket | [`scoop-extras-plus`](#scoop-extras-plus) | Extras-Plus bucket 的 manifest        |
| Scoop bucket | [`scoop-extras-cn`](#scoop-extras-cn)     | Extras-CN bucket 的 manifest          |
