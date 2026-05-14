# Getting Started

本指南帮助你快速上手 TunnelShell。

## 前置要求

- Python 3.10 或更高版本
- SSH 配置文件 (`~/.ssh/config`)
- SSH 密钥认证（推荐）

## 安装

### 从 PyPI 安装

```bash
pip install tunnel-shell
```

### 从源码安装

```bash
git clone https://github.com/yourusername/tunnel-shell.git
cd tunnel-shell
pip install -e .
```

## 配置 SSH

TunnelShell 使用 `~/.ssh/config` 中的主机配置。

### 示例配置

```
# 内网服务器 node3
Host node3
    HostName 10.16.82.202
    Port 22
    User wuxiaoran
    IdentityFile ~/.ssh/id_rsa
    IdentitiesOnly yes

# 通过跳板机连接
Host production
    HostName 192.168.1.100
    User admin
    ProxyJump jump-server
    IdentityFile ~/.ssh/id_production
```

### 验证配置

```bash
# 测试 SSH 连接
ssh node3 'hostname'

# 测试 TunnelShell
tunnel-shell exec --host node3 --cmd 'hostname'
```

## 基本使用

### 1. 执行单条命令

```bash
tunnel-shell exec --host node3 --cmd 'ls -la'
```

输出：
```
✓ Connected to node3
╭─────────────────────────────────── Output ───────────────────────────────────╮
│ total 32                                                                      │
│ drwxr-xr-x  5 user user 4096 May 14 10:00 .                                  │
│ drwxr-xr-x 20 user user 4096 May 14 09:00 ..                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
✓ Exit code: 0
```

### 2. 创建会话

会话允许你在同一个终端上下文中执行多条命令：

```bash
# 创建命名会话
tunnel-shell session create --host node3 --name mysession

# 在会话中执行命令
tunnel-shell session attach --name mysession --cmd 'cd /home/user'
tunnel-shell session attach --name mysession --cmd 'pwd'  # 输出: /home/user

# 清理会话
tunnel-shell session kill --name mysession
```

### 3. 文件传输

```bash
# 上传文件
tunnel-shell file upload --host node3 --local ./config.yaml --remote /tmp/config.yaml

# 下载文件
tunnel-shell file download --host node3 --remote /var/log/app.log --local ./app.log

# 列出远程目录
tunnel-shell file list --host node3 --path /home/user
```

## 进阶使用

### 会话持久化

会话在 detach 后保持运行：

```bash
# 创建会话并启动长时间运行的命令
tunnel-shell session create --host node3 --name longtask
tunnel-shell session attach --name longtask --cmd 'sleep 3600'

# 会话在后台运行，可以稍后重新连接
tunnel-shell session attach --name longtask --cmd 'echo "Still running"'
```

### 多会话管理

```bash
# 创建多个会话
tunnel-shell session create --host node3 --name session1
tunnel-shell session create --host node3 --name session2

# 查看所有会话
tunnel-shell session list

# 输出：
#                              Active Sessions                              
# ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
# ┃ ID               ┃ Name        ┃ Host      ┃ Status  ┃ Created  ┃
# ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
# │ session_xxx      │ session1    │ node3     │ running │ 10:00:00 │
# │ session_yyy      │ session2    │ node3     │ running │ 10:01:00 │
# └──────────────────┴─────────────┴───────────┴─────────┴──────────┘

# 批量清理
tunnel-shell session kill --all
```

### 命令安全检查

在执行危险命令前，先检查安全性：

```bash
tunnel-shell analyze "sudo rm -rf /var/lib/app"

# 输出：
# 
# Command Analysis
#   Raw: sudo rm -rf /var/lib/app
#   Command: rm
#   Args: ['-rf', '/var/lib/app']
#   Category: silent
#
# Security Check
#   Risk Level: high
#   ⚠ Warnings:
#     - Uses sudo
#     - Uses rm -rf
#     - Target path: /var/lib/app
#
#   ⚠ This command requires confirmation
```

### 交互提示检测

检测命令输出中的交互提示：

```bash
tunnel-shell detect "Do you want to continue? [y/N]"

# 输出：
# 
# Prompt Detection
#   Type: confirm
#   Message: Do you want to continue? [y/N]
#   Pattern: [y/N]
#   Action: Send 'y' or 'n' to respond
```

## 常见问题

### Q: SSH 连接失败

检查 SSH 配置：
```bash
# 测试原生 SSH 连接
ssh node3

# 检查 SSH 配置
cat ~/.ssh/config | grep -A10 "Host node3"
```

### Q: 会话丢失

会话存储在 `~/.tunnelshell/sessions/`：
```bash
# 查看会话文件
ls -la ~/.tunnelshell/sessions/

# 查看会话数据
cat ~/.tunnelshell/sessions/sessions.json
```

### Q: 文件传输失败

检查远程路径权限：
```bash
tunnel-shell exec --host node3 --cmd 'ls -la /path/to/dir'
```

## 下一步

- 阅读 [API Reference](api-reference.md) 了解更多命令
- 查看 [Examples](examples.md) 学习实际使用场景
- 阅读 [README](../README.md) 了解项目概述
