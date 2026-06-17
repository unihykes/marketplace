---
name: r2e-code-optimize-unnecessary-copy
description: 检查不必要的对象拷贝并给出低风险替换建议，供code-optimize类型的agent主动调用
disable-model-invocation: true
---

## 指令(做什么)

- 扫描用户指定位置的代码文件。
- 检查是否存在不必要的对象拷贝（可用只读引用或原位使用替代且不改变语义）。
- 给出修复建议（改为 `const auto&`、避免重复拷贝、在保持可读性前提下收敛中间副本）。

## 约束(怎么做)

- [范围] C++ 文件（h/hpp/cpp）
- [命中] 只读场景中按值复制大对象或容器元素，后续未发生修改。
- [命中] 可静态判定“复制后仅用于读取”的局部副本（如 `for (auto x : container)` 中 `x` 仅只读）。
- [排除] 标量或小型 trivially-copyable 类型（如 `int`、`double`、指针、短枚举）默认不标记。
- [排除] 复制语义用于隔离后续修改、延长生命周期或避免悬垂风险时不标记。
- [排除] 需要改动公共接口签名或显著降低可读性的方案不标记。
