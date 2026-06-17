---
name: r2e-code-check-empty-container-access
description: 检查空容器访问风险，供code-check类型的agent主动调用
disable-model-invocation: true
---

## 指令(做什么)

- 扫描用户指定位置的代码文件。
- 在空容器可判前提下检查 `front`/`back` 等越界前访问。
- 给出修复建议（先判空、使用 `if (!v.empty())`、采用 `optional` 式访问或 `at()` 等）。

## 约束(怎么做)

- [范围] C++ 文件（h/hpp/cpp）
- [命中] 在可静态判定为空的同一控制流上，仍调用 `front()`、`back()` 或对 `begin()` 进行未判定解引用。
- [命中] 默认构造或等价空状态后立即进行首末元素访问。
- [排除] 存在有效非空检查且无法证明仍为空，或先 `resize`/`insert` 后访问的合法序不标记。
