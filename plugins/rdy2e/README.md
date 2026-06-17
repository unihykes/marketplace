# r2e

**r2e = Ready to Eat**

这是一个给 Cursor 使用的插件仓库：把规则（rules）、技能（skills）和命令（commands）预先封装好，安装后即可使用。  
`r2e` 的含义是“开袋即食”——对应工程语境就是“开箱即用”。

---

## 概述

在很多团队里，AI 编程能力并不是缺模型，而是缺一套可复用、可传播、可维护的行为标准。  
r2e 想解决的就是这个问题：把散落在对话里的经验，沉淀为可版本化的插件资产。

- **Ready**：规则与技能已预设，不用每次重新解释
- **To Eat**：拿到就能用，减少初始化和对齐成本
- **For Teams**：支持跨仓库复用，保持一致工程行为

一句话：**把 AI 经验做成“即食插件”。**

---

## 仓库内容

- `commands/`：可执行命令定义（`*.md`）
- `rules/`：持久生效的约束与规范（`.mdc`）
- `skills/`：可调用的任务能力（`SKILL.md`）
- `agents/`：可发布的子代理定义（`*.md`）
- `hooks/`：使用自定义脚本来观察、控制和扩展agent行为

---

## 安装与卸载

**当前用户全局** 与 **指定项目** 的安装、卸载见下：无参为全局，一个参数为所给**项目根目录**（不是 `.cursor` 目录本身）。

### Windows

#### 全局（当前用户）

| | 命令 | 结果路径 |
| --- | --- | --- |
| **安装** | `install.bat` | `%USERPROFILE%\.cursor\plugins\local\r2e` |
| **卸载** | `uninstall.bat` | 移除上述全局安装目录 |

#### 指定项目

| | 命令 | 结果路径 |
| --- | --- | --- |
| **安装** | `install.bat "Z:\xxx_path\your_project_path"` | `<项目路径>\.cursor\plugins\local\r2e` |
| **卸载** | `uninstall.bat "Z:\xxx_path\your_project_path"` | 移除该项目的上述目录 |

> 将示例路径 `Z:\xxx_path\your_project_path` 换成你的项目根目录。

### Linux

在仓库根目录执行；若克隆后没有执行权限，可先运行 `chmod +x install.sh uninstall.sh`。

#### 全局（当前用户）

| | 命令 | 结果路径 |
| --- | --- | --- |
| **安装** | `./install.sh` | `$HOME/.cursor/plugins/local/r2e` |
| **卸载** | `./uninstall.sh` | 移除上述全局安装目录 |

#### 指定项目

| | 命令 | 结果路径 |
| --- | --- | --- |
| **安装** | `./install.sh /path/to/your_project` | `<项目路径>/.cursor/plugins/local/r2e` |
| **卸载** | `./uninstall.sh /path/to/your_project` | 移除该项目的上述目录 |

> 参数若以 `~` 或 `~/...` 传入，会按当前用户主目录展开。

---

## 生效与验证

安装后重启 Cursor 即可生效。

然后在 Cursor 的 Rules/Skills 中确认对应组件已加载即可。
