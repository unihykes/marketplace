# 全局
- 所有回复必须使用中文
- 修改代码时,禁止更改源文件的编码格式(例如, 不得将`UTF‑8`转为`GB2312`或其它编码)

# C++代码规范
- 在生成或修改C++代码时, `命名风格`必须遵循文档: <R2U_PLUGIN_ROOT>/contexts/r2u_style_naming.md
- 在生成或修改C++代码时, `格式化风格`必须遵循文档: <R2U_PLUGIN_ROOT>/contexts/r2u_style_code_formatting.md
- 在生成或修改C++代码时, `成员函数定义排版`必须遵循文档: <R2U_PLUGIN_ROOT>/contexts/r2u_style_member_function.md
- 在生成或修改C++代码时, 优先采用较新版本的C++语法和标准库, 详情遵循文档: <R2U_PLUGIN_ROOT>/contexts/r2u_style_modern_cpp.md
- 在生成或修改C++代码时, `日志调用风格`必须遵循文档: <R2U_PLUGIN_ROOT>/contexts/r2u_style_logging.md

# C++头文件依赖
- `rdy2u.h`中包含了常用的std头文件,应该在cpp第一个头文件引用位置用`#include<rdy2u.h>`替代单独引入std头文件
- `rdy2u.h`的接口位于`deps/Linux_e17a3_x64/Release/rdy2u/include/rdy2u.h`
