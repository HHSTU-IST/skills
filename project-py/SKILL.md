---
name: project-py
description: 编写、修改、检查 Python 代码时使用。规定包管理器选择（micromamba/uv，严禁 pip 直装）、代码风格（enumerate、matplotlib 面向对象接口）、以及用 ruff + ty 做静态检查的完整流程。触发词：Python、py、ruff、ty、lint、类型检查、包管理、micromamba、uv、matplotlib、subplots。
agent_created: true
---

# Python 代码编写规则（lectures 仓库）

> 适用范围：`.py` 源码。**不处理 `.ipynb`**。

## 1. 包管理器：先问，再动手（硬规则）

**严禁使用 `pip install` / `pip uninstall` / `pip` 直装。** 任何依赖变动只能通过下面
两者之一完成，且**必须先询问用户选哪一个**：

| 选项 | 追问 | 安装命令（示意） |
| --- | --- | --- |
| `micromamba` / `mamba` | **必须再问具体虚拟环境名** | `micromamba install -n <env> -c conda-forge <pkg> -y` |
| `uv` | 默认仓库内 `.venv` | `uv add <pkg>` / `uv sync` |

当前约定：**micromamba + `kaggle` 环境**。
环境目录**不要写死**，运行时扫描 `PATH` 与环境变量现取：

```bash
command -v micromamba                     # 工具在哪
micromamba env list                       # 有哪些环境、各自路径
micromamba run -n kaggle python -c "import sys; print(sys.prefix)"   # 该环境前缀
```

> 仓库根没有 `pyproject.toml` / `requirements.txt`，依赖一律由 conda 环境承载。

**通用原则：任何文档、脚本、配置里都不写工具或环境的绝对路径，也不写工具版本号。**
需要时现场用 `command -v` / `env list` / `sys.prefix` / `--version` 解析；
`ty.toml` 里也**不要**写死解释器路径。

## 2. 代码风格（写 Python 时必须遵守）

### 基础

**迭代用 `enumerate()`，不要 `range(len())`。**

```python
xs = range(3)
# good
for ind, x in enumerate(xs):
    print(f"{ind}: {x}")
# bad
for i in range(len(xs)):
    print(f"{i}: {xs[i]}")
```

### Matplotlib

1. **用面向对象接口（OO），不要 Artist API。**
2. **画子图用 `plt.subplots(..., constrained_layout=True)`，不要 `plt.tight_layout()`。**

```python
# good
_, axes = plt.subplots(1, 2, constrained_layout=True)
axes[0].plot(x1, y1)
axes[1].hist(x2, y2)
# bad
plt.subplot(121)
plt.plot(x1, y1)
plt.subplot(122)
plt.hist(x2, y2)
```

3. **子图数据可迭代时，用 `axes.flatten()`，不要 `plt.subplot()`。**
4. **迭代对象用 `zip()` / `enumerate()`，不要 `range()`。**

```python
# good
_, axes = plt.subplots(2, 2, figsize=[12, 8], constrained_layout=True)
for ax, x, y in zip(axes.flatten(), xs, ys):
    ax.plot(x, y)
# bad
for i in range(4):
    ax = plt.subplot(2, 2, i + 1)
    ax.plot(x[i], y[i])
```

5. **装饰统一用 `set()` 批量写，不要逐条 `set_*()`。**

```python
# good
ax.set(xlabel="x", ylabel="y")
# bad
ax.set_xlabel("x")
ax.set_ylabel("y")
```

6. **多条 spine 一次传列表，不要逐条调用。**

```python
# good
ax.spines["top", "bottom"].set_visible(False)
# bad
ax.spines["top"].set_visible(False)
ax.spines["bottom"].set_visible(False)
```

> `zip()` 记得显式写 `strict=`（ruff 会要求），避免引入新告警。

## 3. 静态检查：ruff + ty（**改完必须先格式化**）

**顺序固定：① `ruff format` → ② `ruff check` → ③ `ty check`。**
格式化和 lint 是两个不同的动作，`check` 不会替你排版；**改完代码不跑 format 就算没做完**。

```bash
# 0) 先确认工具可用（本机 ruff / ty / micromamba / uv 均在 PATH）
command -v ruff ty micromamba uv

# 1) 格式化 —— 修改后第一步，必须执行
ruff format code python --exclude "*.ipynb"

# 2) 静态检查 —— 只查 .py，排除 notebook
#    根 pyproject 设了 fix=true，必须加 --no-fix
ruff check  code python --no-fix --exclude "*.ipynb"

# 3) 类型检查 —— 必须指向装有依赖的解释器（环境名现取，勿写死路径）
micromamba run -n kaggle ty check code python
```

> **为什么 format 排在最前**：`ruff check --fix` 的自动修复（尤其 `UP` 类升级）
> 常会产生需要重新排版的代码，先 format 可减少二次改动；且 format 只动空白与换行、
> 语义零风险，放第一步不会掩盖后续问题。
>
> ruff **原生会解析 `.ipynb`**，不加 `--exclude "*.ipynb"` 就会把 notebook 也纳入检查。
> 本技能范围仅 `.py`，检查时显式排除。

**注意**：

- **改完必须格式化。** 不要以为 `check` 通过就等于格式正确。
- `ruff check` 默认**会改写文件**（根配置 `fix = true`）。只想检视时加 `--no-fix`。
- `ty` 裸跑会拿系统 Python 当检查环境，普通项目会刷出一片 `unresolved-import` 假警报。
  **务必用 `micromamba run -n <env> ty check ...`**。
- **不要在文档、脚本、配置（含 `ty.toml`）里写工具或环境的绝对路径。**
  路径一律运行时扫描 `PATH` / 环境变量现取，否则换机或升级后必然失效
  （`ty.toml` 写死失效时 ty 会以 `Invalid environment.python setting` 直接 exit 2，
  比不配置更糟）。
- **不要记录工具版本号。** 需要时 `ruff --version` / `ty --version` 现取；
  文档里写死版本会在升级后变成误导信息。
- 不要在子目录新建 `pyproject.toml`，否则该目录会丢掉根 `[tool.ruff.lint]` 的规则集。

## 4. Markdown 文档检查：rumdl（**改完本技能自身的 .md 后必跑**）

本技能是 Markdown 交付物，改动 `SKILL.md` 或 `references/*.md` 后必须用系统环境里的
`rumdl` 检查并修复。

**顺序同样固定：① `rumdl check --fix`（修复）→ ② `rumdl fmt`（格式化）。**

```bash
# 0) 确认可用（在 PATH 中，勿写死路径）
command -v rumdl

# 1) 先看会改什么（只读，务必先做这步）
rumdl check --diff skills/project-py/

# 2) 检查 + 自动修复（范围限定在本技能目录，勿扫全仓）
rumdl check --fix skills/project-py/

# 3) 格式化 —— 修复之后再排版
rumdl fmt skills/project-py/

# 4) 复核
rumdl check skills/project-py/
```

> ⚠️ **自动修复会连坐仓库里其他 `.md`，必须限定路径 + 改完 `git diff` 复核。**
> 实测：即使显式指定 `skills/project-py/`，`rumdl check --fix skills/`
> 之类的不当调用仍会改到 `skills/project-typ/`。**每次 fix 后都要 `git status` 确认
> 只有预期文件被改**，多出来的用 `git checkout -- <path>` 还原。
>
> **安全流程**：`--diff` 预览 → 确认无害再 `--fix` → `git status` 核对范围 → `git diff` 逐行审查。

**注意**：

- **`check` 不带 `-f`/`--fix` 时是只读；带上就会直接改写文件。**
  想先看会改什么，用 `--diff`（只显示差异，不落盘）。
- **`rumdl fmt` 只会修「可自动修复」的问题**，落盘前先用 `--check` 或 `--diff` 预览。
- **范围必须限定到本技能目录。** 不加路径参数会扫全仓，会改动
  `skills/project-typ/` 等无关文件。
- 部分规则**不可自动修复**，需要手改。本技能常见的有三类：

  | 规则 | 含义 | 处理 |
  | --- | --- | --- |
  | `MD013` | 行超长 | 中文长句**不要为凑行宽而硬断**；先看根配置的 `line-length`，必要时行内 disable |
  | `MD036` | 用粗体冒充标题 | 改成真正的 Markdown 标题；若是有序列表项，改用 `1. **…**` 形式 |
  | `MD028` | 引用块内出现空行 | 删掉块内空行，或用 `>` 空行把两段并进同一个引用块 |

- **不要在仓库根新建 `rumdl.toml` 来放宽规则** —— 那会影响其他人的文档；
  局部豁免请用行内 `<!-- rumdl-disable... -->`。

## 5. 检查清单

改完代码后按此顺序执行，**不得跳过格式化那一步**。

- [ ] 依赖变动只经 micromamba（已确认环境名）或 uv，**没有用 pip**
- [ ] 迭代用 `enumerate()` / `zip()`，没有 `range(len())`
- [ ] matplotlib 用 OO 接口 + `constrained_layout=True`
- [ ] 装饰用 `ax.set(...)`、spines 用列表一次性设置
- [ ] **新增内容里没有工具/环境的绝对路径，也没有写死的工具版本号**
- [ ] ① **已执行 `ruff format code python --exclude "*.ipynb"`**
      （输出应为 `left unchanged` 或已完成改写）
- [ ] ② `ruff check code python --no-fix --exclude "*.ipynb"` 无输出
- [ ] ③ `micromamba run -n kaggle ty check code python` 通过（或剩余项均为已记录的存根假警报）

**改动本技能自身的 `.md` 时，追加：**

- [ ] ① 已执行 `rumdl check --fix skills/project-py/`
- [ ] ② 已执行 `rumdl fmt skills/project-py/`
- [ ] ③ `rumdl check skills/project-py/` 无输出（或剩余项已逐条说明为何不改）

## 参考文件

- `references/toolchain.md` —— ruff / ty / micromamba / rumdl 的用法、
  **路径现取方式**、隔离 venv、缓存放雷
