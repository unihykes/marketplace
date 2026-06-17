---
name: r2e-code-check
description: C++ 代码检查，在用户要求 code check 或代码审查时使用
disable-model-invocation: true
---

## 指令(做什么)

你仅允许执行以下代码检查技能:
- 执行技能 `/r2e-code-check-use-after-move`
- 执行技能 `/r2e-code-check-virtual-call-in-constructor`
- 执行技能 `/r2e-code-check-dangling-reference`
- 执行技能 `/r2e-code-check-dangling-std-string-view`
- 执行技能 `/r2e-code-check-dangling-std-span`
- 执行技能 `/r2e-code-check-dangling-lambda-capture`
- 执行技能 `/r2e-code-check-shared-from-this`
- 执行技能 `/r2e-code-check-null-dereference`
- 执行技能 `/r2e-code-check-empty-container-access`
- 执行技能 `/r2e-code-check-out-of-bounds-access`
- 执行技能 `/r2e-code-check-divide-by-zero`
- 执行技能 `/r2e-code-check-sensitive-data-exposure`

## 约束(怎么做)

- 不允许修改源代码。
- 若用户只关心某一原子技能的结果，应优先直接调用对应原子技能。

## 输出

- 逐个输出所有扫描到的文件（不得省略）。
- 无结果时,输出：- <路径>: ok
- 有结果时,输出：- <路径>: <行号[,行号...]>
  - 输出: - 问题: <问题描述>
  - 输出: - 影响: <影响描述>
- 同一文件有多类问题时，按问题分条重复输出该文件路径。