---
name: r2u-code-check-dangling-reference
description: 检查引用绑定临时对象、返回局部引用/指针等悬垂风险；供 code-check 类 agent 主动调用
disable-model-invocation: true
---

## 指令(做什么)

- 扫描用户指定位置的代码文件。
- 检查悬垂引用与悬垂返回风险。
- 给出修复建议（使用具名拥有者、按值返回、延长生命周期、避免返回非 `static` 局部地址等）。

## 约束(怎么做)

- [范围] C++ 文件（h/hpp/cpp）
- [命中] 左值或常量引用绑定到临时对象后仍继续使用。
- [命中] 函数/方法返回指向或引用局部（栈）变量的指针/引用，或返回局部容器 `data()` 等已失效存储。
- [命中] 引用或指针的合法生命周期不覆盖其使用点。
- [排除] 引用/指针生命周期已被显式延长且覆盖使用点时不标记。

## 示例

```cpp
const auto& s = std::string("a") + "b";
use(s);
```

```cpp
const std::string& f() { std::string t = "x"; return t; }
```
