---
name: r2u-code-check-out-of-bounds-access
description: C++ 数组/容器/缓冲区访问，下标或偏移可静态证明越界（>= size 或 < 0）；供 code-check 类 agent 主动调用
disable-model-invocation: true
---

## 指令(做什么)

- 扫描用户指定位置的代码文件。
- 在静态可判的数组、容器、SIMD 或缓冲区访问中检查索引是否越界。
- 给出修复建议（改用 `at`、先比较 `size`、使用 `std::array` + 编译期边界、`span` + 子域、或修正下标常量）。

## 约束(怎么做)

- [范围] C++ 文件（h/hpp/cpp）
- [命中] 在下标或偏移可静态估计的访问中，索引/指针偏移已可证明 `>= size` 或 `< 0`。
- [命中] 典型场景包括定长 `std::array`、栈数组、`vector` 常量下标、已知长度 C 串常量下标等。
- [排除] 仅运行时索引且无法静态证明越界的路径不强行标记。
