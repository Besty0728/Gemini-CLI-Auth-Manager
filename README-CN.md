# Gemini CLI 账号管理器

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-2.0-brightgreen.svg)

**Gemini CLI 账号管理器** 是一个轻量级且强大的工具，专为 Google Gemini CLI 环境设计。支持多账号秒级切换、**配额耗尽时自动轮换账号**、以及**统一号池管理**！

> 📖 [English Version (英文版本)](./README.md)

---

## ✨ 功能特性

- **一键秒切账号**: 瞬间在多个账号之间切换
- **自动备份凭证**: 切换时自动保存你的凭据信息
- **🆕 配额自动切换**: 检测到配额耗尽时自动轮换到下一个账号
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

### 如何更新

如果你已经安装过旧版本，可以通过以下步骤更新：

1. 在项目目录运行 `git pull` 同步最新代码。
2. 重新运行 `python install.py` 覆盖安装（推荐，可同步最新 Hook 逻辑）。
3. 或手动将 `quota_auto_switch.py` 拷贝至 `~/.gemini/` 目录下。

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

# 策略管理
gchange strategy             # 查看当前策略
gchange strategy conservative       # 设置为保守模式
gchange strategy gemini3-first      # 设置为 Gemini3 优先模式

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

---

## 🎯 交互式菜单

运行 `gchange menu` 打开交互式配置界面：

```
  Menu:
  ----------------------------------------
  1. Switch Account
  2. Switch to Next Account
  3. Change Strategy
  4. Configure Auto-Switch
  5. Toggle Auto-Switch (Enable/Disable)
  6. Manage Account Pool
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

## 🔄 自动切换功能

当检测到 API 返回配额错误（429）时，系统会自动：
1. 切换到下一个账号
2. 自动重试当前请求
3. 通知用户切换结果

### 配置选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `enabled` | 是否启用自动切换 | `true` |
| `strategy` | 轮换策略 | `gemini3-first` |
| `threshold` | 触发切换的配额阈值 (%) | `5` |
| `max_retries` | 最大重试次数 | `3` |

### 策略对比

| 策略 | 触发条件 | 适用场景 |
|------|---------|---------|
| `conservative` | 所有模型配额 ≤ 阈值 | 充分利用每个账号 |
| `gemini3-first` | 任一 Gemini 3.x ≤ 阈值 | 偏好最新模型 |

---

## ❓ 常见问题

### Q: 自动切换支持检测哪些错误？

Hook 会自动检测以下情况并触发账号切换：

| 错误类型 | 示例消息 |
|---------|---------|
| HTTP 429 | `429 Too Many Requests` |
| 配额耗尽 | `Resource exhausted`, `Quota exceeded` |
| CLI 提示 | `Usage limit reached for all Pro models` |
| 等待重置 | `Access resets at 11:55 PM GMT+8` |
| 选择界面 | `1. Keep trying  2. Stop` |

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

## ❤️ 贡献

欢迎提交 Issue 或 PR 来改进这个项目！
