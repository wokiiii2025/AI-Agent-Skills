# Goal Contract Patterns

Source: OpenAI Cookbook, "Using Goals in Codex", published May 9, 2026.
URL: https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex

Adapted for WorkBuddy: Goal 创建由 TaskCreate/TaskUpdate 任务体系实现，不再依赖 Codex 的 create_goal/get_goal 工具。

Use this file when designing unusual Goals, explaining why a Goal is strong or weak, converting a vague target into a questionnaire, or handling confirmation and launch edge cases.

## Contents

- Core Model
- Six Required Fields
- Strength Checklist
- Interview Decision Tree
- Question Bank
- Output Skeleton
- Confirmation and Launch Cases
- Example Transformations
- Behavior Checklist

## Core Model

A Goal is a thread-scoped completion contract. It keeps the agent working toward a defined outcome across turns and requires concrete evidence before completion.

Use Goals when:

- The finish line is clear but the path is uncertain.
- The next action depends on what the agent learns after tests, logs, code inspection, benchmarks, generated artifacts, or research evidence.
- The task may need continuation: debugging, optimization, dependency migration, flaky test investigation, multi-step refactor, evidence-backed research, reproduction, audit, or final artifact creation.

Prefer a normal prompt when:

- The user wants a one-line edit, simple explanation, short review, or single answer.
- The finish line is vague and cannot be verified.
- The user wants brainstorming rather than evidence-checked completion.

## Six Required Fields

| Field | Purpose | Question to ask |
|---|---|---|
| Outcome | Defines what is true when done | What exact end state do you want? |
| Verification surface | Defines proof | Which test, command, artifact, log, benchmark, or source proves it? |
| Constraints | Prevents regressions | What must stay unchanged or green? |
| Boundaries | Limits scope | Which files, repos, tools, data, or sources may be used? |
| Iteration policy | Guides continuation | After each attempt, how should the agent choose the next action? |
| Blocked stop condition | Defines honest stopping | When should the agent stop and what should it report? |

## Strength Checklist

A strong Goal:

- Names a measurable or inspectable outcome.
- Names a verification surface.
- Preserves key constraints.
- Gives boundaries without prescribing every step.
- Says how to iterate after failed attempts.
- Defines what to report if blocked.
- Lets evidence, not confidence, decide completion.

A weak Goal:

- Says "improve", "refactor", "fix", "research", or "make better" without an audit surface.
- Has no evidence standard.
- Has no non-regression constraints.
- Requires exact proof when only approximate evidence may exist.
- Encourages endless continuation without a stop condition.

## Interview Decision Tree

Do not use the six fields as a fixed questionnaire. Recompute the next question after every answer.

1. Extract everything already present in the request and supplied materials.
2. Resolve the parent decision that changes the remaining questions, usually Outcome or Verification.
3. Ask one question when later questions depend on its answer.
4. Batch up to three questions only when they are independent.
5. Give a recommended answer and the relevant tradeoff.
6. Stop when all remaining uncertainty can be represented honestly as an assumption, an iteration-time experiment, or a blocked condition.

Look up facts with authorized read-only tools instead of asking the user. Ask the user to decide preferences, risk tolerance, permissions, and acceptance thresholds.

## Question Bank

Use at most three questions per round. Prefer concrete choices.

Outcome:

- 完成后，哪句话必须是真的？
- 你要的是修复、优化、产物、审计报告，还是排查到明确阻塞？
- 有没有硬指标，比如延迟、通过率、文件数量、准确率、覆盖范围？

Verification:

- 用什么验收？测试命令、benchmark、生成文件、截图、日志、数据表，还是人工检查？
- 有没有必须运行的命令或必须通过的 validator？
- 如果证据不完整，允许哪些代理证据？

Constraints:

- 推进时哪些东西不能变？公开 API、原文内容、现有设计、数据状态、兼容性、成本、速度？
- 哪些测试或行为必须保持绿色？
- 有没有不能碰的文件或不能做的操作？

Boundaries:

- 允许修改哪些目录或模块？
- 可以联网吗？可以用哪些来源？
- 可以创建新文件、脚本、报告或自动化吗？

Iteration:

- 第一轮失败后，是优先最小改动、先复现、先定位瓶颈、还是先建立证据清单？
- 每轮需要记录什么：改了什么、证据显示什么、下一步为什么？
- 要不要先做只读调查，再动手？

Blocked:

- 什么情况下应该停下来，不继续猜？
- 卡住时你希望看到什么：尝试路径、证据、失败原因、需要你补的输入？
- 预算/时间/轮数有没有上限？

## Output Skeleton

````markdown
待启动 Goal vN

我理解的目标：...

**字段拆解**：
- Outcome:
- Verification:
- Constraints:
- Boundaries:
- Iteration:
- Blocked:

**执行路线图**：
1. [子任务1] → 产出：...；验收：...
2. ...

假设/待确认：
- ...

为什么适合 Goal：
...

启动：
- 只设计模式：不启动。
- 设计并启动模式：回复"开始"或"确认并启动 Goal vN"。
````

## Confirmation and Launch Cases

| Situation | Required behavior |
|---|---|
| User asks only for a prompt | Produce the plan draft; do not create tasks. |
| User says "看起来不错" | Treat it as feedback, not launch authorization. |
| User confirms the unique latest vN | Use TaskCreate to create the sub-tasks, then start executing the first one. |
| User changes the draft | Increment to vN+1, show the full new text, and require confirmation again. |
| Same objective is already active | Check TaskList; if tasks already exist for this Goal, continue them. |
| A different unfinished Goal exists | Report the conflict; ask the user to resolve existing tasks or start fresh. |
| Tasks contain destructive or external actions | Starting execution does not waive the normal approval boundary. |
| A task is blocked | Keep it in_progress, report evidence and blocker, request unlock input. |
| A task is completed | Mark it completed with TaskUpdate only when Verification surface is satisfied. |
| All tasks completed | Run VERIFY: check every Verification item has evidence before declaring done. |

## Example Transformations

Weak:

> Improve performance

Strong:

> Reduce p95 checkout latency below 120 ms, verified by the checkout benchmark, while keeping the correctness suite green. Use only the checkout service, benchmark fixtures, and related tests. Between iterations, record what changed, what the benchmark showed, and the next best experiment to try. If the benchmark cannot run or no valid paths remain, stop with the attempted paths, evidence gathered, blocker, and next input needed.

Weak:

> Write docs for this feature

Strong:

> Produce a docs page for Goals that explains the lifecycle, command surface, and two examples. Verify that the page builds locally and that all referenced commands match current CLI behavior. Preserve existing docs style and source links. Between iterations, compare the page against the checklist and fix the highest-impact gap first. If blocked, stop with the draft, missing inputs, and exact decision needed.

Research:

> Produce the strongest evidence-backed reproduction of <paper/project> using the available materials and local resources. Attempt every headline result where feasible, verify outputs where possible, and end with a report that separates reproduced mechanics, approximate trained results, blocked exact replay, and remaining uncertainty. If original seeds, paths, checkpoints, or source state are unavailable, label that limitation instead of claiming exact recovery.

## Behavior Checklist

Use these cases when validating GoalGo behavior:

- A complete request produces Draft v1 without unnecessary questions.
- A vague request asks no more than three high-impact questions per round.
- Partial answers are accumulated and are not asked again.
- "你来定" produces conservative, explicitly labeled assumptions.
- Design-only mode makes zero TaskCreate calls.
- Editing v1 invalidates its confirmation and produces v2.
- Confirming vN uses TaskCreate to create sub-tasks, then immediately starts executing.
- A blocked task stays in_progress with evidence reported, not silently marked complete.
- A completed task has Verification surface evidence before being marked completed.
- All tasks completed triggers VERIFY step before declaring Goal done.
- A successful launch is followed by a real first step, not only a status message.
