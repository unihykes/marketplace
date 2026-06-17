---
name: r2e-code-check-dangling-std-string-view
description: 检查 std::string_view 绑定临时或即将失效缓冲的悬垂风险；供 code-check 类 agent 主动调用
disable-model-invocation: true
---

## 指令(做什么)

- 扫描用户指定位置的代码文件。
- 检查是否存在将 `std::string_view` 绑定到临时、已释放、已移动或即将销毁拥有者的风险。
- 给出修复建议（延长为具名 `std::string` 等拥有者、在表达式内用完、或同步失效后的视图）。

## 约束(怎么做)

- [范围] C++ 文件（h/hpp/cpp）
- [命中] `std::string_view` 指向临时 `std::string`、临时容器或临时返回值内部缓冲，语句结束后缓冲失效。
- [命中] `std::string_view` 指向已 `move` 或已销毁拥有者曾持有的缓冲。
- [命中] 在 `realloc` 或容器收缩等可能使引用失效后仍持有旧 `std::string_view`。
- [排除] 本技能仅负责 `std::string_view`。
- [排除] `std::span` 同类问题不在本技能内，交由 `/r2e-code-check-dangling-std-span` 处理。

## 示例

```cpp
std::string_view sv = get_tmp_str();
use(sv);
```
