---
name: r2e-code-check-dangling-lambda-capture
description: 检查 lambda 按引用捕获局部等导致的悬垂风险；供 code-check 类 agent 主动调用
disable-model-invocation: true
---

## 指令(做什么)

- 扫描用户指定位置的代码文件。
- 检查是否存在按引用捕获局部（或等效于引用局部）的 lambda 被延长生命周期使用的风险。
- 给出修复建议（按值捕获、将数据移入 `shared_ptr`、或确保同步与作用域）。

## 约束(怎么做)

- [范围] C++ 文件（h/hpp/cpp）
- [命中] lambda 按引用捕获局部变量，且 lambda 生命周期长于该局部变量生命周期。
- [命中] lambda 被交给线程、异步回调、定时器或长生命周期持有者，存在延后执行。
- [排除] lambda 不逃逸当前作用域，或改为按值捕获时不标记。

## 示例

```cpp
int x = 0;
std::thread([&x]() { use(x); }).detach();
```
