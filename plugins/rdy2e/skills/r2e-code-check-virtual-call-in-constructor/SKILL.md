---
name: r2e-code-check-virtual-call-in-constructor
description: 检查构造阶段虚调用风险，供code-check类型的agent主动调用
disable-model-invocation: true
---

## 指令(做什么)

- 扫描用户指定位置的代码文件。
- 仅当同时满足本技能定义的三条命中条件时报告问题。
- 给出替代建议（改为非虚辅助函数、类名限定的 `Base::f()` 调用、或使用 CRTP/两阶段初始化等可审计方案）。

## 约束(怎么做)

- [范围] C++ 文件（h/hpp/cpp）
- [命中] 调用发生在构造函数或析构函数语义路径内（含其可判定的直接/间接调用路径）。
- [命中] 被调用成员函数在该类声明中为 `virtual`（含 `override` 的虚重载）。
- [命中] 调用未使用类名显式限定（即非 `Base::func()` 形式）。
- [排除] 调用目标不是 `virtual` 成员函数，不触发该项。
- [排除] 使用类名限定的静态分派调用 `virtual` 成员（如 `Base::virtual_func()`）不报警。

## 示例

```cpp
struct Base {
  Base() { init(); }  // 若 init 为 virtual 且未用 Base::init() 则命中
  virtual void init() {}
  virtual ~Base() { cleanup(); }
  virtual void cleanup() {}
};
```
