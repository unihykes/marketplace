---
name: r2u-code-build
description: C++ 代码构建，在用户要求 code build 时使用
disable-model-invocation: false
---

## 指令(做什么)

- 必须在工作区根目录包含 `cmake/` 的 C++ 工程根目录下执行。
- 先执行日志创建命令，并读取返回 JSON 中的 `log_path` 和 `agent_message`。
  `python3 <R2U_PLUGIN_ROOT>/skills/common/r2u_create_logfile.py --skill r2u_code_build`
- 然后将上一步 JSON 中的 `log_path` 作为 `<R2U_LOG_PATH>` 传入构建命令。
  `python3 <R2U_PLUGIN_ROOT>/skills/r2u-code-build/scripts/r2u_code_build.py --logpath=<R2U_LOG_PATH> --module <相对路径> --kind=<debug | release>`

- `--module` 与 `--kind` 均可省略、顺序任意。
- 省略 `--module`（或为空）表示编译全部模块。
- 省略 `--kind` 时默认 `debug`（不区分大小写）；`release` 必须显式写出。

## 约束(怎么做)

- [禁止解读] 除对占位字段 `<...>` 替换外，不得读取指令内脚本内容。
- [运行提示] 执行日志创建命令后，必须立即向用户转述 `agent_message`和`log_path`。
- [日志限制] 构建运行期间禁止读取 `log_path` 指向的日志原文。
- [终端模式] 强制使用前台模式运行，`block_until_ms` 设置为 `86400001` 毫秒。
