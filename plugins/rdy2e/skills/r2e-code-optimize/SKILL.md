---
name: r2e-code-optimize
description: C++ 代码优化编排技能，在用户要求代码优化、代码清理或降噪整理时使用
disable-model-invocation: true
---

## 指令(做什么)

你仅允许执行以下代码优化技能:
- 执行技能 `/r2e-code-optimize-unused-symbol`
- 执行技能 `/r2e-code-optimize-unnecessary-copy`
- 执行技能 `/r2e-code-optimize-unnecessary-temporary`

## 约束(怎么做)

- 不允许修改源代码。
- 若用户只关心某一原子技能的结果，应优先直接调用对应原子技能。

## 输出

- 逐个输出所有扫描到的文件（不得省略）。
- 无结果时,输出：<路径>: ok
- 有结果时,输出：<路径>: <行号[,行号...]>
    - 问题: <问题描述>
    - 影响: <影响描述>
- 同一文件有多类问题时，按问题分条重复输出该文件路径。