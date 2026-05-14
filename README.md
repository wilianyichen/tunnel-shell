# TunnelShell

[![PyPI version](https://badge.fury.io/py/tunnel-shell.svg)](https://pypi.org/project/tunnel-shell/)
[![Python](https://img.shields.io/pypi/pyversions/tunnel-shell.svg)](https://pypi.org/project/tunnel-shell/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Agent-first remote terminal with persistent PTY sessions**

TunnelShell 让 AI Agent 像操作本地终端一样操作远程服务器，支持 PTY 会话持久化、attach/detach/reconnect、文件传输、多会话管理。

## 为什么需要 TunnelShell？

传统 SSH 工具对 AI Agent 不友好：
- 每次执行命令都是「盲操作」——发命令、等结果、断开
- 无法处理交互式命令（sudo 密码、确认提示、REPL）
- 无法维持上下文（cd 之后路径丢失、环境变量不延续）
- 调试困难，看不到「终端里发生了什么」

TunnelShell 解决这些问题：
- **PTY 会话持久化** - attach/detach/reconnect
- **多会话管理** - 命名、共享、恢复
- **终端状态检测** - ready/running/password/confirm/repl
- **文件传输集成** - upload/download/list
- **超时控制与安全机制** - 多级超时、危险命令阻止

## 安装

```bash
pip install tunnel-shell
```

或从源码安装：

```bash
git clone https://github.com/yourusername/tunnel-shell.git
cd tunnel-shell
pip install -e .
```

## 快速开始

### 1. 单命令执行

```bash
tunnel-shell exec --host node3 --cmd 'hostname'
```

### 2. 会话管理

```bash
# 创建会话
tunnel-shell session create --host node3 --name deploy

# 在会话中执行命令
tunnel-shell session attach --name deploy --cmd 'ls -la'

# 列出所有会话
tunnel-shell session list

# 终止会话
tunnel-shell session kill --name deploy
tunnel-shell session kill --all
```

### 3. 文件传输

```bash
# 上传文件
tunnel-shell file upload --host node3 --local file.txt --remote /tmp/file.txt

# 下载文件
tunnel-shell file download --host node3 --remote /tmp/file.txt --local file.txt

# 列出远程目录
tunnel-shell file list --host node3 --path /home/user
```

## 主机配置

TunnelShell 使用 `~/.ssh/config` 中的主机配置：

```
Host node3
    HostName 10.16.82.202
    Port 22
    User wuxiaoran
    IdentityFile ~/.ssh/id_rsa
```

## 功能特性

### PTY 会话持久化

会话在 detach 后保持运行，可以重新连接：

```bash
# 创建会话
tunnel-shell session create --host node3 --name mysession

# 执行命令后 detach（会话保持）
tunnel-shell session attach --name mysession --cmd 'top'

# 重新连接
tunnel-shell session attach --name mysession --cmd 'q'
```

### 多会话管理

```bash
# 创建多个会话
tunnel-shell session create --host node3 --name session1
tunnel-shell session create --host node3 --name session2

# 查看所有会话
tunnel-shell session list

# 批量清理
tunnel-shell session kill --all
```

### 命令安全检查

```bash
# 分析命令安全性
tunnel-shell analyze "sudo rm -rf /tmp/test"

# 输出：
# Risk Level: medium
# Warnings: Uses sudo, Uses rm -rf
```

### 交互提示检测

```bash
# 检测文本中的交互提示
tunnel-shell detect "Password:"

# 输出：
# Prompt Type: password
# Message: Password:
```

### 会话录制

```bash
# 列出录制
tunnel-shell recording list

# 查看录制详情
tunnel-shell recording show session_id

# 导出录制
tunnel-shell recording export session_id -o output.txt
```

## CLI 命令

```bash
tunnel-shell --help

Commands:
  exec       Execute a single command on a remote host
  session    Session management (create/attach/list/kill)
  file       File transfer operations (upload/download/list)
  analyze    Analyze a command for classification and safety
  detect     Detect interactive prompts in text
  recording  Session recording operations
```

## 使用场景

### 远程部署

```bash
tunnel-shell session create --host node3 --name deploy
tunnel-shell session attach --name deploy --cmd 'cd /app && git pull'
tunnel-shell session attach --name deploy --cmd 'docker-compose up -d'
tunnel-shell session kill --name deploy
```

### 日志查看

```bash
tunnel-shell exec --host node3 --cmd 'tail -100 /var/log/syslog'
```

### 文件同步

```bash
tunnel-shell file upload --host node3 --local config.yaml --remote /app/config.yaml
```

## 开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/tunnel-shell.git
cd tunnel-shell

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 构建文档
cd docs && make html
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- [paramiko](https://github.com/paramiko/paramiko) - SSH 库
- [click](https://github.com/pallets/click) - CLI 框架
- [rich](https://github.com/Textualize/rich) - 终端美化
