---
name: r2u-unify-log-style
description: 统一代码中的日志风格，确保日志格式、级别和输出方式符合项目规范
disable-model-invocation: true
---

## 指令(做什么)

- 扫描用户指定位置的代码文件。
- 检查日志语句的风格一致性（格式字符串、参数传递方式）。
- 识别不符合项目日志规范的写法并给出修正建议。
- 在用户确认后可直接修改代码以统一日志风格。

## 约束(怎么做)

- 仅适用于C++ 文件（h/hpp/cpp）;
- 在代码内输出日志时优先使用r2u基础库提供的日志宏:r2u_debug, r2u_info, r2u_warn,_r2u_error;
- 日志宏的格式如下:
    r2u_info("do something", var1, var2, var2);
    其中第1个参数固定为消息事件,不要使用任何的格式化字符(%或者{}等), 消息事件中不需要主动写变量列表.消息事件最好是一个自然语句.
    第2个至N个参数是可选参数,表示变量列表,r2u宏会通过编译时反射自动将其变量名称以json格式输出在日志中
    例如上述日志输出内容是 [2026-07-06 12:09:00 300689 +08:00] [demo] [592272] [592272] [info] [demo.cpp:10] test() do something {"var1": 1, "var2", 2, "var3": 3}
    r2u_info宏的变量列表接受大部分原始类型,不需要做fmt::ptr(xxx)转换
    如果变量列表是函数调用或者比较长,可以使用r2u_named给变量重命名以便精简输出.

## 示例
- 当用户指定位置代码文件内日志文件不符合r2u格式时进行整改.
例1:
r2u_info("this[{}], mUpdateTimestamp[{}], mSwanUnitCreatePolling[{}]", (void *)this, mUpdateTimestamp, mSwanUnitCreatePolling);
需要整改为:
r2u_info("", this, mUpdateTimestamp, mSwanUnitCreatePolling);

例2:
r2u_error("init sam kv lun for storePool[{}] exception[{}]", getStorePoolInfo(storePoolInfo), e.toFullString());
需要整改为:
r2u_error("init sam kv lun", r2u_named(pool, getStorePoolInfo(storePoolInfo)), r2u_named(error, e.toFullString()));

例3:
r2u_error(_T("storePoolID[%s] not found."), storePoolID.c_str());
需要整改为
r2u_error("store pool not found.", storePoolID);