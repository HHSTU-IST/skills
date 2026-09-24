---
name: anchor-french
description: >
  交互式法语角主持资料生成器，面向「≤10 人、90 分钟」固定规格的**平等圆桌讨论**。每次调用先通过提问确认本次「核心语法点」「参与者水平」「规模」；话题从题库选择 / 随机一个 / 自定义输入。随后生成一页沉浸式法文主持脚本：主持词穿插 30 个按话题分 3 部分递进、带 DELF/DALF 语法等级标注的讨论问题；并按词性分类生成生词表。触发词：法语角、French corner、主持法语角、法语口语、法语讨论、法语话题、法语会话。
agent_created: true
---

# 法语角主持助手（French Corner Host）

**技能类型**：混合型 —— 硬约束管「这不做什么」（平等圆桌、仅法语、固定 90 分钟规格），工序管「先问清楚再产出」的 intake 与生成工作流。

为每周法语角生成一套**可直接朗读/使用**的主持材料。交互式：先问清楚本次要练什么，再产出。

本文档**只描述流程、风格与方法论**，不含任何可选项数据——语法点、水平、规模、话题维度、时间分配、词汇量、DELF/DALF 等级等一律以 `assets/fr-corner-config.json` 为准。增删选项只改 JSON，无需改动本文件。

## 1. 定位与硬约束

- **形式定位（最重要）**：**平等参与的圆桌讨论**。所有参与者地位相同，**不含任何辅导 / 教学环节、无分组讨论、不布置作业**。主持人以「参与者之一」的身份引导话题与节奏，不讲解语法、不做一对一纠正、不充当教师。
- **语言范围**：**仅法语**。本技能包只加载 `assets/fr-corner-config.json`，不含西语数据与逻辑；西语角请用独立技能包 `anchor-spanish`。
- **规模与时长**：**≤10 人 / 固定 90 分钟**（来自 `constraints.max_participants`、`constraints.duration_minutes`）。
- **水平范围**：B1–C2（含「混合（B1–C2）」），不出现 A1 / A2。
- **产出物**：单页 Markdown 主持脚本，路径模板见 `style.output_path_template`（`docs/fr-{topic}.md`）。

## 2. 技能包结构与运行

本包是**自包含技能包**（skill-creator 标准结构）：脚本、参考文档、数据资产齐备，只服务法语，可整体复制到 `~/.workbuddy/skills/` 使用。标准布局、各文件的职责边界、运行时管线（谁解析、谁收集、谁产出）与顶层字段的消费方，都在 `references/corner-architecture.md`（§0 / §1.6，本包实例取值见 §5）；本节只留跑得起来的那部分。

```bash
# 在技能包根目录执行
python scripts/corner_config.py          # 加载并校验 assets/fr-corner-config.json
python scripts/corner_skill.py           # 驱动 intake 并导出简报
python scripts/corner_audit.py           # schema / 身份 / 文档 ↔ 配置 / 纯度审计
```

`corner_audit.py` 是唯一的机械闸门，四段依次跑、任一段失败即非零退出：schema 引用 → 包身份 →
本文件 ↔ 配置取值 → 内容纯度。

## 3. 交互契约（intake）

用 **AskUserQuestion** 收集；编排由 `question_plan` 驱动，**逐题询问（一问一答）**。若用户在消息里已给全，可跳过对应题。

| #  | 语义键              | 内容           | 类型 | 上限 | 依赖 | 询问方式                                       |
| -- | ------------------- | -------------- | ---- | ---- | ---- | ---------------------------------------------- |
| Q1 | `grammar_primary`   | 核心一级语法点 | 多选 | 2    | —    | 询问                                           |
| Q2 | `grammar_secondary` | 核心二级语法点 | 多选 | —    | Q1   | 询问（选项由 Q1 动态决定）                     |
| Q3 | `level`             | 参与者水平     | 单选 | 1    | —    | 询问                                           |
| Q4 | `topics`            | 话题           | 多选 | 2    | —    | 询问：`topic_pool` 题库 / 🎲 随机一个 / 自定义 |
| Q5 | `scale`             | 参与规模       | 单选 | 1    | —    | 询问                                           |

交互原则：

- 选项一律**鼠标可勾选**；单题选项数超过 `constraints.ask_options_per_question`（6）时，按「每 ≤6 个一组」拆成多个子问题（同一语义键，标题标注 `（i/n）`）。
- 优先用选项给出推荐，同时允许用户自定义（"Other"）。
- **不要替用户脑补语法点**；Q1 未答则 Q2 不展开。
- **话题三种来源（Q4 逐题询问）**：① 从 `topic_pool` 题库勾选；② 选「🎲 随机选一个」，由 `random_topics()` 从题库抽取；③ 直接输入自定义话题（`allow_custom`）。用户若在消息里已给话题，以其为准，不再追问。

## 4. 工作流

### 4.1 读取简报

先读**当前工作目录**下的 `fr-corner-brief.md`（文件名见 `meta.brief_filename`，由 `scripts/corner_skill.py` 的 `export_brief()` 落盘），从中取得水平、一 / 二级语法点、话题、规模、词汇量目标、阶段名、POS 分组、DELF/DALF 标注规则与 rubric。**简报已确定的参数不再询问**。

### 4.2 生成主持词（纯法文；30 题穿插其中）

输出为**一页可朗读的主持脚本**：问题不单列成块，而是穿插在主持词中、由引出语自然带出。

- **开场（Ouverture）**：欢迎语（法文）→ 点明本次语法点 + 话题 + 目标。
- **破冰（Brise-glace）**：一句轻松小问让全员开口，直接并入 Partie 1 第 1 题。
- **话题引入（Thème）**：简述话题背景（法文），过渡到第一部分。
- **讨论（Discussion，含 30 题，分 3 部分）**：
  - 每部分以一个**主持引出句**开场（如 « Passons à la partie suivante : … »）；
  - 该部分 10 题**逐题由主持过渡语引出**（如 « À tour de rôle, répondez : » / « Et vous, qu'en pensez-vous ? »），问题本身仅法文 + DELF/DALF 标注；
  - 三部分按话题相似度聚类、内部递进（个人化 → 展开 → 辩论），难度随题号递增。
- **结语（Clôture）**：复述要点（法文）→ 预告下次（**无作业**）。

### 4.3 30 题生成规则（DELF/DALF 标注 · 按话题聚类 · 递进）

围绕话题与语法点，**先按话题相似度聚成 3 个部分**（用户已给话题时按其子主题拆；如旅行 → 「过往经历 / 理想旅行 / 旅行与社会」）。**每个部分内部保持递进**：个人化、易开口 → 开放式展开 → 观点 / 辩论，难度随题号递增。

- 每题标注 DELF/DALF 等级，标签形如 `(DELF B1)` / `(DELF B2)` / `(DALF C1)` / `(DALF C2)`；仅使用 B1–C2 档，不出现 A1 / A2。映射规则与 rubric 取自配置的 `exam`（`levels` / `rules` / `rubric`），并已写入简报。
- 「混合」水平时按 B1→C2 梯度高低搭配，每部分内避免连续同档。
- **不再单列「热身 / 深入 / 辩论」区块**，递进体现在部分内部与主持词穿插中。
- **语言**：问题本身**仅保留法文**（不附中文括注）；由主持人现场口译。

示例结构（共 3 部分，每部分 10 题，嵌入主持词）：

- Partie 1（话题 A，递进 DELF B1→DELF B2）
- Partie 2（话题 B，递进 DELF B1→DALF C1）
- Partie 3（话题 C，递进 DELF B1→DALF C2）

### 4.4 生成生词表（按词性 · 法文释义）

分组取自 `style.pos_groups`：Noms / Verbes / Adjectifs / Adverbes / Prépositions·Conjonctions / Pronoms / Autres。

每组：`mot → définition en français → exemple en français`（不使用中文；词性分类名也用法文）。优先覆盖话题与语法所需高频词，总量按简报中的 `vocab_targets` 区间控制。

### 4.5 产出与呈现

- 写入**单个 Markdown 文件**，路径按 `style.output_path_template`（`docs/fr-{topic}.md`，`{topic}` 为法文话题名，如 旅行 → `docs/fr-voyage.md`）；目录不存在则创建；若不在该仓库工作，写到当前工作区 `./docs/`。
- 固定生成「环节时间分配」表（数值取自 `time_allocation`，见附录 A.5）。
- 写入后**尝试执行 `rumdl fmt <文件路径>`** 格式化；若 `rumdl` 不可用或报错，静默跳过（不阻断产出）。
- 用 **present_files** 打开预览，并附一句简要说明。

## 5. 风格约定

- **纯法文（无中文・无英文）**：主持词正文、问题、生词释义、例句，以及所有标题、结构化标签（Ouverture / Brise-glace / Thème / Discussion / Clôture）与词性分类名一律用法文书写。可保留 `(DELF B1)`、`(DALF C1)` 这类等级标注（属法文专有名词）。
- **不使用水平分割线 `---`**（`style.no_hr`）：区块之间用标题层级与空行分隔。
- **用标题代替整行加粗**（`style.no_full_line_bold`）：元信息 / 小节标题使用 `##` / `###`，禁止用整行 `**加粗**` 充当标题（避免 rumdl MD036 告警）。
- 难度贴合所选水平；例句尽量贴近话题场景；问题明确标注 DELF/DALF 等级。

## 附录 A · 生成框架与方法（无法数据化的部分）

> 以下为方法论：话题生成、30 题框架、题型骨架、句型复杂度、规模备注。
> 所有**可选项数据**以 `assets/fr-corner-config.json` 为准，由 `scripts/corner_config.py` 加载；增删选项只改 JSON。

### A.1 话题生成方法（适用于任何语法点）

不限定具体话题。选定语法点后，按「三个通用生活维度」生成 2–4 个候选话题，保证任意语法点都能落地。

做法：取该语法点的「典型使用场景」，套入任一维度即可。例如条件式 → 「理想旅行 / 假设情景 / 礼貌请求」，被动语态 → 「新闻事件 / 环保 / 社会议题」。用户可自定义，无需受限于示例。

若用户说「没想好 / 随便 / 你来定」，直接用上述维度为该语法点生成 2 个话题，不再追问。

> 三个通用生活维度（个人经历 / 日常、愿望 / 假设、社会 / 比较 / 观点）及其示例已外置为 `topic_dimensions`（label + desc），供话题生成时参考；Q4 的备选题库则来自 `topic_pool`。

### A.2 30 题生成框架（3 部分递进，适用于任何话题）

先按「话题相似度」把 30 题聚成 3 个部分（每部分 10 题）。若用户给了 1 个话题，可用「个人 → 展开 → 社会 / 观点」三维度拆分；若给了 2 个话题，可各占部分或合并。

每部分内部保持递进（本规格水平 B1–C2，不出现 A1 / A2）：

1. 第 1–3 题：封闭、个人化、易开口（`(DELF B1)`）
2. 第 4–7 题：开放式展开，融入更复杂语法（`(DELF B1)–(DELF B2)`）
3. 第 8–10 题：观点 / 辩论，引入抽象与论证（`(DELF B2) / (DALF C1) / (DALF C2)`）

通用引导句（可复用，把 {S} 替换为本次话题）：

- 开场引出：*Passons à la partie suivante : {S}.*
- 逐题过渡：*À tour de rôle, répondez :* / *Et vous, qu'en pensez-vous ?*
- 递进示例：*Parlez de {S} selon votre expérience.* → *Qu'est-ce qui a marqué votre {S} ?* → *Faut-il changer notre rapport à {S} ?*

### A.3 按语法点的题型骨架（通用，可替换话题）

每条语法点给出 3 档难度骨架；使用时把 {S} 换成本次话题，并打上对应 DELF / DALF 标签：

| 语法点      | 易（B1）骨架                                 | 中（B2）骨架                                 | 难（C1 / C2）骨架                                    |
| ----------- | -------------------------------------------- | -------------------------------------------- | ---------------------------------------------------- |
| 复合过去时  | *Qu'est-ce que tu as fait à propos de {S} ?* | *Raconte une anecdote concernant {S}.*       | *En quoi {S} a-t-il changé ta vision des choses ?*   |
| 条件式      | *Si tu avais…, que ferais-tu pour {S} ?*     | *Que conseillerais-tu à quelqu'un sur {S} ?* | *Et si {S} n'existait plus, comment vivrions-nous ?* |
| 虚拟式      | *Il faut que tu… pour {S}.*                  | *Je doute que {S} soit facile.*              | *Bien qu'on dise que {S}, …*                         |
| 比较级      | *Préfères-tu {S} ou {S2} ?*                  | *En quoi {S} est-il meilleur que {S2} ?*     | *Quel modèle de {S} l'emporte ?*                     |
| 介词 à / de | *De quoi parle-t-on quand on dit {S} ?*      | *C'est à / de {S} que je pense.*             | *À quel point {S} t'appartient-il ?*                 |
| 疑问句      | *Que penses-tu de {S} ?*                     | *Comment expliques-tu {S} ?*                 | *Jusqu'où irait-on pour {S} ?*                       |
| 宾语代词    | *Tu l'as fait pour {S} ?*                    | *On nous l'a expliqué à propos de {S}.*      | *Ce qu'on en a retenu de {S}…*                       |
| 将来时      | *Que feras-tu pour {S} ?*                    | *Quand commenceras-tu {S} ?*                 | *À quoi ressemblera {S} dans dix ans ?*              |
| en / y      | *Tu en as beaucoup parlé, de {S}.*           | *J'y pense souvent, à {S}.*                  | *En tirer parti de {S} : comment ?*                  |
| 被动        | *{S} est souvent mal compris.*               | *Cela a été décidé à propos de {S}.*         | *Comment {S} est-il perçu par la société ?*          |
| 连词从句    | *Parce que {S}…*                             | *Bien que {S}, …*                            | *À condition que {S}, que ferions-nous ?*            |
| 数字 / 量词 | *Combien de {S} ?*                           | *La plupart des {S} sont…*                   | *Quel est le juste équilibre de {S} ?*               |
| 现在分词    | *En {S}, on apprend…*                        | *{S}, c'est en agissant qu'on comprend.*     | *Tout en {S}, il faut aussi…*                        |

> 骨架仅供启发；实际生成时结合话题与所选水平微调。

### A.4 词汇量与句型复杂度（B1–C2）

词汇量区间以 `vocab_targets` 为准（当前：B1 25–35 / B2 28–40 / C1·C2 40–55 / 混合 25–55 词）。各水平句型复杂度：

- B1：条件式 / 虚拟式入门、连贯叙述
- B2：复杂从句、被动
- C1 / C2：抽象论证、语体转换
- 混合：分档标注

### A.5 环节时间分配与规模备注（固定 90 分钟）

数值以 `time_allocation` 为准（解析器会校验：分钟合计须等于 `scales.minutes`，pct 合计须 ≈ 1.0）：

| 环节                                | 占比  | 分钟 |
| ----------------------------------- | ----- | ---- |
| 开场（Ouverture）                   | 11.1% | 10   |
| 破冰（Brise-glace）                 | 6.7%  | 6    |
| 话题引入（Thème）                   | 15.6% | 14   |
| 讨论（Discussion，含 3 部分 30 题） | 55.5% | 50   |
| 结语（Clôture）                     | 11.1% | 10   |

> 规格固定为 **≤10 人 / 90 分钟** 的平等圆桌，**不含辅导 / 教学环节、无分组讨论**。小班（2–4 人）可加重讨论、压缩开场；大班（9–10 人）可改为全员轮流发言。
