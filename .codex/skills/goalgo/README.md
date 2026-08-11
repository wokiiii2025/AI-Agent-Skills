# GoalGo

GoalGo 把普通需求变成可验证、可追踪、可诚实停止的执行计划。说出需求后，它会快速复述、追问关键问题、累积答案、生成待确认的计划草案；你确认后，它会拆解为子任务并启动执行，最后用证据验收。

```text
需求 → 关键反问 → 待启动计划 v1 → 你确认 → 拆任务执行 → 用证据验收
```

## 快速安装

> 用户只需发一句：「帮我安装 goalgo：https://github.com/Backtthefuture/goalgo」
> AI 会自动识别当前平台，拉取对应版本。

| 你在哪个平台 | AI 应该拉取 | 安装目标路径 |
|---|---|---|
| **Codex** | 根目录 `/` | Codex skills 目录（`npx skills add`） |
| **WorkBuddy** | `/workbuddy` 子目录 | `~/.workbuddy/skills/goalgo/` |

**AI 安装逻辑**：读取本 README 的「两个版本」章节，根据当前运行环境选择对应版本。Codex 环境拉根目录，WorkBuddy 环境拉 `workbuddy/` 子目录。

## 两个版本

| 版本 | 目录 | 适用平台 | 核心机制 |
|---|---|---|---|
| **Codex 版** | 根目录 `/` | OpenAI Codex | 调用 `create_goal` / `get_goal` Goal API |
| **WorkBuddy 版** | `/workbuddy` | 腾讯 WorkBuddy | 用 `TaskCreate` / `TaskUpdate` 任务体系驱动 |

两个版本共享相同的核心方法论（六字段 Goal contract、累积 ledger、确认门控、提问策略），区别在于执行层如何落地：

- **Codex 版**：确认后调用 `create_goal` 创建 Goal 对象，由 Codex Goal 系统跨轮持续推进。
- **WorkBuddy 版**：确认后用 `TaskCreate` 把计划拆为 3-7 个可追踪子任务，用 `TaskUpdate` 管理状态和依赖，最后新增 VERIFY 步骤对照验收标准逐项检查。

---

## Codex 版

GoalGo 是一个给 Codex 使用的 Goal 设计与启动 Skill。

你只需要说出需求并调用 `$goalgo`。它会先理解材料、快速追问关键问题、把答案整理成可验证的 Goal；等你确认最终版本并回复"开始"后，再真正启动 Goal 执行。

## 30 秒安装

### 1. 安装前准备

你需要：

- 已安装并能正常使用 Codex。
- 能打开终端：macOS 使用“终端”，Windows 使用 PowerShell。
- 终端里能运行 `npx --version`。

如果提示找不到 `npx`，先从 [Node.js 官网](https://nodejs.org/)安装 Node.js，再重新打开终端。

### 2. 复制安装命令

把下面整行复制到终端并回车：

```bash
npx -y skills@latest add Backtthefuture/goalgo --skill goalgo --agent codex -g -y
```

这会把 GoalGo 全局安装到 Codex，之后在不同项目里都能使用。

如果只想安装到当前项目，使用：

```bash
npx -y skills@latest add Backtthefuture/goalgo --skill goalgo --agent codex -y
```

### 3. 检查是否装好

```bash
npx -y skills@latest list -g --agent codex
```

看到 `goalgo` 就表示安装成功。如果 Codex 侧栏暂时没有出现它，新建一个 Codex 任务或重启 Codex 刷新列表。

## 1 分钟上手

### 最简单的调用方式

在需求后面加上 `$goalgo`：

```text
我想把一批访谈资料整理成一份对外发布的行业报告。

$goalgo
```

GoalGo 会自动：

1. 用简单的话复述目标。
2. 从已有需求和材料中提取已知信息。
3. 每轮最多问 3 个真正影响结果的问题。
4. 累积你的回答，不重复问已经确认的内容。
5. 生成一个 `待启动 Goal v1` 给你检查。

### 想让它确认后直接运行

推荐这样写：

```text
我想把一批访谈资料整理成一份对外发布的行业报告。

$goalgo
先快速问清楚，再生成最终 Goal 给我确认。我说“开始”后，直接启动并执行。
```

回答完问题后，GoalGo 会展示最终 Goal。确认没有问题，只需回复：

```text
开始
```

它会检查当前任务里有没有冲突的 Goal，创建并核验新 Goal，然后马上执行第一项工作。

## 完整使用示例

你输入：

```text
我有一个 60 分钟访谈视频和转写稿，想整理成一篇适合公众号发布的文章。

$goalgo
问清楚后生成最终 Goal。我说“开始”后直接运行。
```

GoalGo 可能会问：

```text
1. 最终文章希望多长，主要给谁看？
2. 用什么证明完成：Markdown 文件、来源检查，还是你人工验收？
3. 哪些原话、事实或文件绝对不能改？
```

你回答后，它会生成：

```text
待启动 Goal v1

/goal <完整的结果、验收、约束、边界、迭代和阻塞条件>

启动：回复“开始”或“确认并启动 Goal v1”。
```

你回复“开始”，Goal 才会真正运行。

## GoalGo 适合什么任务

适合：

- 调试复杂 Bug 或不稳定测试。
- 性能优化、迁移和重构。
- 多步骤研究、审计和证据核验。
- 生成需要反复检查的报告、网页、文档或其他产物。
- 第一条路径失败后还要根据证据继续尝试的任务。

通常不需要 Goal：

- 改一句话。
- 回答一个简单问题。
- 做一次很短的代码修改。
- 只想头脑风暴，还没有明确完成标准。

遇到这些情况，GoalGo 会建议直接使用普通提示词。

## 常见问题

### 为什么它没有立刻执行？

这是正常的。GoalGo 会先把最终 Goal 展示给你，只有你明确回复“开始”“确认并启动”或“按这版运行”才会启动。类似“看起来不错”“先这样”不会被当成启动授权。

### 为什么提示已有 Goal？

同一个 Codex 任务里不能同时创建两个未完成 Goal。请先完成或清除原 Goal，或者新建一个 Codex 任务再运行。

### `$goalgo` 没有出现在列表里怎么办？

先运行安装检查命令；如果已经能看到 `goalgo`，新建一个 Codex 任务或重启 Codex。

### Goal 会不会自动删除文件或发布内容？

不会因为启动 Goal 就自动获得更多权限。删除文件、发布内容、发送消息、修改线上数据或读取敏感资料，仍然遵守 Codex 原有的授权和安全规则。

## 更新与卸载

更新 GoalGo：

```bash
npx -y skills@latest update goalgo -g -y
```

卸载 GoalGo：

```bash
npx -y skills@latest remove goalgo -g -y
```

## Skill 文件

- [`SKILL.md`](./SKILL.md)：GoalGo 的完整工作流。
- [`references/goal-contract-patterns.md`](./references/goal-contract-patterns.md)：Goal 模板、反问方式和启动边界。
- [`agents/openai.yaml`](./agents/openai.yaml)：Codex 界面元数据。

---

## WorkBuddy 版

WorkBuddy 版是对 Codex 原版的适配优化，将 Codex 专有的 `create_goal` / `get_goal` 工具调用替换为 WorkBuddy 原生的 `TaskCreate` / `TaskUpdate` / `TaskList` 任务体系。

### 与 Codex 版的区别

| 改造点 | Codex 版 | WorkBuddy 版 |
|---|---|---|
| PREFLIGHT 启动前检查 | 检查 `get_goal` / `create_goal` 可用性 | 删除（WorkBuddy 无此工具） |
| LAUNCH 启动执行 | 调用 `create_goal` 传 objective | 用 `TaskCreate` 拆为 3-7 个可追踪子任务 |
| VERIFY 证据验收 | 无独立步骤，依赖 Goal 工具自动核验 | 新增：全任务完成后对照 Verification surface 逐项检查 |
| DRAFT 输出格式 | `/goal <body>` 命令行格式 | 计划草案（六字段 + 执行路线图） |

**保留不变的核心方法论**：六字段 Goal contract、累积 ledger、确认门控、提问策略、强弱 Goal 判定。

### 安装

#### 方式一：在 WorkBuddy 对话中一句话安装

在 WorkBuddy 对话里直接说：

```text
帮我安装 WorkBuddy 版的 goalgo：https://github.com/Backtthefuture/goalgo
```

WorkBuddy 会自动拉取仓库的 `workbuddy/` 目录并安装到 `~/.workbuddy/skills/goalgo/`，装完后新建对话即可使用。

#### 方式二：终端一行命令安装

```bash
curl -fsSL https://raw.githubusercontent.com/Backtthefuture/goalgo/main/install-workbuddy.sh | bash
```

脚本会自动 clone 仓库、复制 `workbuddy/` 到 `~/.workbuddy/skills/goalgo/`。如果已有旧版会自动备份。

#### 方式三：手动安装

```bash
git clone https://github.com/Backtthefuture/goalgo.git /tmp/goalgo
cp -r /tmp/goalgo/workbuddy ~/.workbuddy/skills/goalgo
rm -rf /tmp/goalgo
```

安装完成后，重启 WorkBuddy 或新建对话即可生效。

### 使用方式

在 WorkBuddy 对话中直接说出需求，Skill 会自动触发：

```text
我想把一批访谈资料整理成一份对外发布的行业报告。
先快速问清楚，再生成最终计划给我确认。我说"开始"后，直接拆任务执行。
```

回答完关键问题后，它会展示「待启动计划 vN」，包含六字段拆解和执行路线图。确认后回复：

```text
开始
```

它会用 TaskCreate 创建子任务、设置依赖、标记首个任务为进行中，然后立即开始执行。

### WorkBuddy 版 Skill 文件

- [`workbuddy/SKILL.md`](./workbuddy/SKILL.md)：适配 WorkBuddy 的完整工作流。
- [`workbuddy/references/goal-contract-patterns.md`](./workbuddy/references/goal-contract-patterns.md)：适配后的 Goal 模板和确认边界。
- [`workbuddy/agents/workbuddy.yaml`](./workbuddy/agents/workbuddy.yaml)：WorkBuddy 界面元数据。
