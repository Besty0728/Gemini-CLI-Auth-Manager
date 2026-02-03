# Gemini CLI 账号管理器

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-2.1-brightgreen.svg)

**Gemini CLI 账号管理器** 是一个轻量级且强大的工具，专为 Google Gemini CLI 环境设计。支持多账号秒级切换、**配额预检测自动轮换**、以及**统一号池管理**！

> ⚠️ **重要提示**: 由于 Gemini CLI 的缓存机制，**账号切换后必须重启 CLI** 才能生效！(按 Ctrl+C 两次退出，重新运行 gemini)

> 📖 [English Version (英文版本)](./README.md)

---

## ✨ 功能特性

- **一键秒切账号**: 瞬间在多个账号之间切换
- **自动备份凭证**: 切换时自动保存你的凭据信息
- **🆕 配额预检测**: 实时检测配额，支持多种策略（耗尽所有/耗尽指定系列）
- **🆕 号池管理**: 统一查看、添加、删除账号
- **🆕 交互式菜单**: 可视化配置界面，轻松管理所有设置
- **完美集成斜杠命令**: 在 Gemini CLI 中作为 `/change` 命令无缝集成

---

## 🚀 安装指南

```bash
git clone https://github.com/Besty0728/Gemini-CLI-Auth-Manager.git
cd gemini-auth-manager
python install.py
```

### 依赖项

```bash
pip install requests
```

### 如何更新

如果你已经安装过旧版本，可以通过以下步骤更新：

1. 在项目目录运行 `git pull` 同步最新代码。
2. 重新运行 `python install.py` 覆盖安装（推荐，可同步最新 Hook 逻辑）。

---

## 🛠 使用方法

### 命令速查

```bash
# 查看账号列表
gchange

# 切换账号
gchange 1                    # 切换到第 1 个账号
gchange user@gmail.com       # 通过邮箱切换
gchange next                 # 切换到下一个账号

# 交互式菜单（推荐）
gchange menu

# 号池管理
gchange pool                 # 查看号池
gchange pool add             # 添加账号（交互式）
gchange pool add user@gmail.com    # 添加指定账号
gchange pool remove 2        # 删除第 2 个账号
gchange pool import ~/creds.json   # 导入凭证文件

# 配置管理
gchange config               # 查看所有配置
gchange config enabled true  # 启用自动切换
gchange config threshold 10  # 设置阈值为 10%
```

### 斜杠命令（Gemini CLI 内部）

```text
/change           # 查看所有账号
/change 1         # 切换到第 1 个账号
/change next      # 切换到下一个账号
```

### 配额查询工具

```bash
# 直接查询当前账号的配额状态
python quota_api_client.py
```

输出示例：
```
📊 Gemini CLI 配额状态
======================================================================
模型                           剩余配额        重置时间
----------------------------------------------------------------------
gemini-2.5-flash               🟢 93.3%        (重置于 10h 20m 后)
gemini-3-pro-preview           🟡 33.5%        (重置于 1h 10m 后)
gemini-2.5-pro                 🟡 33.5%        (重置于 1h 10m 后)
======================================================================
```

---

## 🎯 交互式菜单

运行 `gchange menu` 打开交互式配置界面：

```
  Menu:
  ----------------------------------------
  1. Switch Account
  2. Switch to Next Account
  3. Configure Auto-Switch
  4. Toggle Auto-Switch (Enable/Disable)
  5. Manage Account Pool
  0. Exit
```

---

## 📦 号池管理

### 查看号池

```bash
gchange pool
```

输出示例：
```
Account Pool Overview:
--------------------------------------------------
  01. user1@gmail.com                    ● Active
  02. user2@gmail.com                    ○ Standby
  03. user3@gmail.com                    ○ Standby
--------------------------------------------------
  Total: 3 accounts
```

### 添加账号

```bash
# 交互式添加
gchange pool add

# 直接添加
gchange pool add newuser@gmail.com
```

### 删除账号

```bash
# 按编号删除
gchange pool remove 2

# 按邮箱删除
gchange pool remove user2@gmail.com
```

### 导入凭证

```bash
gchange pool import /path/to/oauth_creds.json
```

---

## 🔄 配额预检测（BeforeAgent Hook）

系统通过 Google Code Assist API 实时检测配额状态：

```
用户发送请求
    ↓
BeforeAgent Hook 触发
    ↓
调用 Google API 获取配额剩余百分比
    ↓
检测到 Pro 模型 < 10%
    ↓
自动调用 gchange next 切换账号
    ↓
显示切换提示，用户重新发送请求
```

### 配置选项

编辑 `~/.gemini/auth_config.json`：

```json
{
  "auto_switch": {
    "enabled": true,
    "threshold": 10,
    "cache_minutes": 5,
    "models_to_check": ["gemini-3-pro-preview", "gemini-2.5-pro"]
  }
}
```

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `enabled` | 是否启用自动切换 | `true` |
| `threshold` | 触发切换的配额阈值 (%) | `10` |
| `cache_minutes` | 配额缓存时间（分钟） | `5` |
| `models_to_check` | 监控的模型列表 | Pro 模型 |

### 注意事项

- **切换后需重启 CLI**：由于 Gemini CLI 在启动时加载 OAuth 凭证，切换账号后当前会话不会立即使用新账号
- **提示信息**：切换成功后会显示提示，请重新发送您的请求

---

## ❓ 常见问题

### Q: 切换账号后为什么需要重启 CLI？

这是 Gemini CLI 的设计限制。OAuth 客户端在 CLI 启动时初始化并缓存，切换 `oauth_creds.json` 文件后，需要重新启动 CLI 才能加载新凭证。

### Q: 自动切换支持检测哪些情况？

| 检测方式 | 说明 |
|----------|------|
| **配额预检测** (BeforeAgent) | 通过 API 实时检测配额百分比 |
| **错误后检测** (AfterAgent) | 检测 429 错误、配额耗尽消息等 |

### Q: 出现 403 VALIDATION_REQUIRED 错误怎么办？

这是 Google 账户验证问题，不是切换工具的问题。

**解决步骤**：
1. 访问错误信息中的验证链接
2. 登录对应的 Google 账户并完成验证
3. 或删除凭证重新登录：`rm ~/.gemini/oauth_creds.json && gemini`

### Q: 如何手动切换语言？

```bash
# 编辑配置文件
# ~/.gemini/auth_config.json 中添加 "language": "cn" 或 "en"
```

---

## 📁 文件结构

```
~/.gemini/
├── oauth_creds.json          # 当前账号凭证
├── auth_config.json          # 配置文件
├── gemini_cli_auth_manager.py # 核心管理脚本
├── gchange.bat               # 命令行入口
├── accounts/                 # 账号凭证池
│   ├── user1@gmail.com.json
│   ├── user2@gmail.com.json
│   └── ...
├── hooks/
│   ├── quota_pre_check.py    # BeforeAgent Hook
│   └── quota_auto_switch.py  # AfterAgent Hook
└── commands/
    └── change.toml           # 斜杠命令配置
```

---

## ❤️ 贡献

欢迎提交 Issue 或 PR 来改进这个项目！
