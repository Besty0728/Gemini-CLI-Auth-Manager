# Gemini CLI 账号管理器

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-2.5-brightgreen.svg)

**Gemini CLI 账号管理器** 是一个专为 Google Gemini CLI 环境设计的轻量级工具。它支持极速多账号切换、**配额耗尽自动轮换**，以及**统一的账号池管理**！

> 📖 [English Version](./README.md)

---

## ✨ 核心特性

- **极速切换**：秒级完成多个 Google 账号之间的身份验证切换。
- **自动备份**：切换时自动保存当前凭据，防止丢失。
- **🆕 Gemini 3.1 系列支持**：完全兼容最新的 `gemini-3.1-pro` 和 `gemini-3.1-flash-lite` 模型。
- **🆕 智能轮换策略**：
  - `gemini3.1-series-only` (默认)：监控所有 3.1 模型配额。
  - `gemini3.1-pro-only`：仅在 3.1 Pro 模型配额不足时触发切换。
  - `custom`：支持通过正则表达式自定义监控的模型。
- **配额预检**：通过 Google API 实时监控配额，在耗尽前自动切换（默认阈值 10%）。
- **原生 OAuth 登录**：支持通过浏览器一键登录，官方认证并直接捕获账号到号池。
- **交互式菜单**：可视化的配置与管理界面 (`gchange menu`)。
- **斜杠命令**：完美集成到 Gemini CLI 中，使用 `/change` 直接调用。

---

## 🚀 快速安装

```bash
git clone https://github.com/Besty0728/Gemini-CLI-Auth-Manager.git
cd Gemini-CLI-Auth-Manager
python install.py
```

### 依赖要求
- Python 3.8+
- `requests` 库 (`pip install requests`)
- Gemini CLI 已安装，并可通过 PATH 中的 `gemini` 命令调用

### Linux/macOS 说明
- 安装器会创建 `~/.gemini/gchange`，并在可行时链接到 `~/.local/bin/gchange`。
- 如果安装后找不到 `gchange` 命令，请把下面内容加入你的 shell 配置：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## 🛠 使用方法

### 1. 斜杠命令 (在 Gemini CLI 内部使用)
| 命令 | 说明 |
| :--- | :--- |
| `/change <n>` | 切换到序号为 n 的账号 |
| `/change next` | 切换到下一个可用账号 |
| `/change menu` | 打开交互式管理菜单 |
| `/change strategy` | 查看或更改轮换策略 |
| `/change config` | 快速查看自动切换配置 |

### 2. 终端命令
| 命令 | 说明 |
| :--- | :--- |
| `gchange` | 列出所有账号及当前状态 |
| `gchange <n>` | 快速切换到序号为 n 的账号 |
| `gchange menu` | 进入交互式菜单（推荐） |
| `gchange pool login` | 通过 OAuth 添加新账号 |

---

## ⚙️ 配置说明

配置文件位于 `~/.gemini/auth_config.json`。

| 配置项 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `strategy` | `gemini3.1-series-only` | 可选：`conservative`, `gemini3.1-pro-only`, `gemini3.1-series-only`, `custom` |
| `threshold` | `10` | 剩余配额低于 10% 时触发切换 |
| `model_pattern` | `gemini-3.1.*` | 用于匹配监控模型的正则表达式 |
| `auto_restart` | `false` | 切换后是否自动重启 CLI，取决于当前平台能否启动 `gemini` |

---

## 📂 项目结构

```text
~/.gemini/
├── gemini_cli_auth_manager.py  # 核心管理脚本
├── auth_config.json            # 配置文件
├── google_accounts.json        # 账号索引元数据
├── auth_profiles/              # 账号凭据存储文件夹
│   ├── user1@gmail.com/
│   └── ...
├── hooks/
│   ├── quota_pre_check.py      # BeforeAgent 钩子（请求前检查）
│   └── quota_auto_switch.py    # AfterAgent 钩子（响应后处理）
└── commands/
    └── change.toml             # 斜杠命令配置文件
```

---

## 📅 更新日志 (Changelog)

### [v2.5] - 2026-05-06
- **🛠 修复**: 修正安装说明中的目录名（`cd Gemini-CLI-Auth-Manager`），确保在 Linux 和 macOS 等大小写敏感系统上步骤可正确执行。（感谢 @getbot887，closes #5）

### [v2.4] - 2026-05-03
- **🌍 跨平台**: 新增 Linux 和 macOS 兼容性 — Unix 启动器、动态平台检测、子进程调用使用 `sys.executable`。（感谢 @bincat233）
- **🛠 修复**: 正确处理引号包裹的组合命令，如 `'pool login'`。（感谢 @victorinfinops）
- **🛠 修复**: `auto_restart` 配置项现可通过 `gchange config` 设置。

### [v2.3] - 2026-03-22
- **✨ 增强**: 全面更新 UI 和 内部逻辑至 2.3 版本。
- **✨ 优化**: 改进了配额监控的响应速度和准确性。
- **🛠 修复**: 解决了 2.2 版本中已知的几处残留引用和显示问题。
- **🚀 安装程序**: 升级安装程序以支持更可靠的挂钩配置。

### [v2.2] - 2026-02-15
- **🆕 Gemini 3.1 支持**: 增加对 `gemini-3.1-pro` 和 `gemini-3.1-flash-lite` 的自动轮换支持。
- **🆕 智能策略**: 引入 `gemini3.1-series-only` 等轮换策略。
- **⚡ 自动轮换**: 实现基于配额预检的自动账号切换。

---

## ❤️ 贡献与反馈
由 Besty 开发。欢迎提交 Issue 或 PR！
