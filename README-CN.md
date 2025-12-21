# Gemini CLI 账号管理器

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Gemini CLI 账号管理器** 是一个轻量级且强大的工具，专为 Google Gemini CLI 环境设计。只需一条命令，即可在多个账号间实现秒级切换！

> 📖 [English Version (英文版本)](./README.md)

---

## ✨ 功能特性

- **一键秒切账号**: 瞬间在多个账号之间切换。
- **自动备份凭证**: 切换时自动保存你的凭据信息。
- **交互式管理菜单**: 查看活跃账号、保存的配置文件和历史记录。
- **完美集成斜杠命令**: 在 Gemini CLI 中作为 `/change` 命令无缝集成。
- **智能双语安装**: 支持英文和中文的智能设置脚本。

---

## 🚀 安装指南

### 1. 下载
下载本仓库或克隆到本地：
```bash
git clone https://github.com/Besty0728/Gemini-CLI-Auth-Manager.git
cd gemini-auth-manager
```

### 2. 安装
运行安装脚本，它会自动为你配置好所有环境。
```bash
python install.py
```
> 根据提示选择你的语言（英文或中文）。

---

## 🛠 使用方法

### 方式 1: Gemini CLI（斜杠命令）
在 Gemini 聊天界面中：

```text
/change 1                # 切换到第 1 个账号
/change user@gmail.com   # 通过邮箱切换
/change                  # 列出所有账号
/change menu             # 打开交互式管理菜单（添加/删除）
```

### 方式 2: Windows 终端（CMD/PowerShell）
在普通的命令行终端中：

```bash
# 列出账号列表
gchange

# 快速切换

gchange 2
gchange user@gmail.com
```

---

## ❤️ 贡献
欢迎提交 Issue 或 PR 来改进这个项目！
