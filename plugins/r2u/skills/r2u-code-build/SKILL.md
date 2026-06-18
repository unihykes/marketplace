---
name: r2u-code-build
description: C++ 代码构建，在用户要求 code build 时使用
disable-model-invocation: false
---

## 指令(做什么)

- 必须在工作区根目录包含 `cmake/` 的 C++ 工程根目录下执行。
- 先执行预运行准备命令，并接收返回 JSON 信息，用占位符 `<R2U_OPTIONS>` 接收。
  `python3 <R2U_PLUGIN_ROOT>/skills/common/r2u_prerun.py --skill r2u_code_build`
- 将 JSON 信息作为参数直接传递给构建脚本。
  `python3 <R2U_PLUGIN_ROOT>/skills/r2u-code-build/scripts/r2u_code_build.py --options=<R2U_OPTIONS> --module <相对路径> --kind=<debug | release>`

- `--module` 与 `--kind` 均可省略、顺序任意。
- 省略 `--module`（或为空）表示编译全部模块。
- 省略 `--kind` 时默认 `debug`（不区分大小写）；`release` 必须显式写出。

## 约束(怎么做)

- [禁止解读] 除对占位字段 `<...>` 替换外，不得读取指令内脚本内容。
- [运行提示] 执行预运行准备命令后，必须立即向用户转述返回的 `R2U_OPTIONS` 信息。
- [禁止解读] 构建运行期间禁止解读 `R2U_OPTIONS` 信息的原文。
- [终端模式] 强制使用前台模式运行，`block_until_ms` 设置为 `86400001` 毫秒。
