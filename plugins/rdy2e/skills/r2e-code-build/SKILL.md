---
name: r2e-code-build
description: C++ 代码构建，在用户要求 code build 时使用
disable-model-invocation: false
---

## 指令(做什么)

- 须在工作区根为含 `cmake/` 的 C++ 工程根目录下执行。

  `python3 <技能路径>/scripts/r2e_code_build.py --module <相对路径> --kind=<debug | release>`

- `--module` 与 `--kind` 均可省略、顺序任意。
- 省略 `--module`（或为空）表示编译全部模块；
- 省略 `--kind` 时默认 `debug`（不区分大小写）；`release` 须显式写出。

## 约束(怎么做)
- [禁止解读] 除对占位字段 `<...>` 替换外，不得读取指令内脚本内容。
- [终端模式] 强制使用前台模式运行，`block_until_ms` 设置为 `86400001` 毫秒。
