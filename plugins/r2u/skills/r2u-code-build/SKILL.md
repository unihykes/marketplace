---
name: r2u-code-build
description: C++ 代码构建，在用户要求 code build 时使用
disable-model-invocation: false
---

## 指令(做什么)

- 必须在工作区根目录包含 `cmake/` 的 C++ 工程根目录下执行。

#### 1.执行 `r2u_prerun` 脚本
```shell
  `R2U_OPTIONS="$(python3 <R2U_PLUGIN_ROOT>/skills/common/r2u_prerun.py --skill r2u_code_build)"`
```
- 执行`prerun`命令结束后，必须立即向用户原样输出 `${R2U_OPTIONS}`

#### 2.执行`r2u_run`脚本
```shell
  `python3 <R2U_PLUGIN_ROOT>/skills/r2u-code-build/scripts/r2u_code_build.py --options="${R2U_OPTIONS}" --module <相对路径> --kind=<debug | release>`
```
- 执行`r2u_run`脚本可能耗时很长, 为规避超时中断,agent可以每30秒获取一次日志文件的最后一行内容,并原样输出给用户(添加系统时间作前缀).
- 参数`--module` 与 `--kind` 均可省略、顺序任意。
- 省略 `--module`（或为空）表示编译全部模块。
- 省略 `--kind` 时默认 `debug`（不区分大小写）；`release` 必须显式写出。

## 约束(怎么做)

- [禁止解读] 除对占位字段 `<...>` 替换外，不得读取指令内脚本内容。
- [禁止解读] 构建运行期间禁止解读 `R2U_OPTIONS` 内可能出现的日志文件内容。
- [终端模式] 强制使用前台模式运行，`block_until_ms` 设置为 `86400001` 毫秒。
