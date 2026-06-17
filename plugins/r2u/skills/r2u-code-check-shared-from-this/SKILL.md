---
name: r2u-code-check-shared-from-this
description: 检查裸 this 构造 shared_ptr、误用 shared_from_this 等风险；供 code-check 类 agent 主动调用
disable-model-invocation: true
---

## 指令(做什么)

- 扫描用户指定位置的代码文件。
- 检查是否存在在不适用类型上从 `this` 直接构造 `shared_ptr` 或误用 `shared_from_this` 的风险。
- 给出修复建议（使用 `enable_shared_from_this` + 工厂、统一由 `shared_ptr` 入口创建、或采用弱引用等）。

## 约束(怎么做)

- [范围] C++ 文件（h/hpp/cpp）
- [命中] 在未建立与现有控制块关联的类型上，用裸 `this` 直接构造 `std::shared_ptr` 或等效方式创建第二控制块。
- [命中] 对尚未由 `std::shared_ptr` 接管的对象调用 `shared_from_this()`。
- [排除] 类公开继承 `std::enable_shared_from_this`，且对象先由 `shared_ptr` 拥有后再调用 `shared_from_this()` 的合法模式不标记。
