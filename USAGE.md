# TunnelShell 使用指南

## 快速开始

TunnelShell 是一个 Agent-first 的远程终端工具，支持：
- SSH 远程命令执行
- PTY 会话持久化
- 文件传输
- 多会话管理

## 安装

```bash
pip install tunnel-shell
```

或从源码安装：
```bash
cd /root/project/tunnel-shell
pip install -e .
```

## 可用主机

- `node3` - 内网服务器 (10.16.82.202)

## 常用命令

### 1. 单命令执行

```bash
tunnel-shell exec --host node3 --cmd '<command>'
```

示例：
```bash
tunnel-shell exec --host node3 --cmd 'hostname'
tunnel-shell exec --host node3 --cmd 'df -h'
tunnel-shell exec --host node3 --cmd 'docker ps'
```

### 2. 会话管理

创建会话：
```bash
tunnel-shell session create --host node3 --name <session_name>
```

连接会话并执行命令：
```bash
tunnel-shell session attach --name <session_name> --cmd '<command>'
```

列出所有会话：
```bash
tunnel-shell session list
```

终止会话：
```bash
tunnel-shell session kill --name <session_name>
tunnel-shell session kill --all
```

### 3. 文件传输

上传文件：
```bash
tunnel-shell file upload --host node3 --local <local_path> --remote <remote_path>
```

下载文件：
```bash
tunnel-shell file download --host node3 --remote <remote_path> --local <local_path>
```

列出远程目录：
```bash
tunnel-shell file list --host node3 --path <remote_path>
```

### 4. 命令分析

分析命令安全性：
```bash
tunnel-shell analyze "sudo rm -rf /tmp/test"
```

检测交互提示：
```bash
tunnel-shell detect "Password:"
```

## 使用场景

### 场景1：快速查看服务器状态

```bash
tunnel-shell exec --host node3 --cmd 'uptime && free -h && df -h'
```

### 场景2：部署应用

```bash
# 创建部署会话
tunnel-shell session create --host node3 --name deploy

# 执行部署命令
tunnel-shell session attach --name deploy --cmd 'cd /home/wuxiaoran/app'
tunnel-shell session attach --name deploy --cmd 'git pull'
tunnel-shell session attach --name deploy --cmd 'docker-compose up -d'

# 清理
tunnel-shell session kill --name deploy
```

### 场景3：日志查看

```bash
tunnel-shell exec --host node3 --cmd 'tail -100 /var/log/syslog'
```

### 场景4：文件同步

```bash
# 上传配置文件
tunnel-shell file upload --host node3 --local config.yaml --remote /home/wuxiaoran/app/config.yaml

# 下载日志文件
tunnel-shell file download --host node3 --remote /home/wuxiaoran/logs/app.log --local ./app.log
```

## 注意事项

1. 会话会持久化，记得用 `session kill` 清理
2. 使用 `--cmd` 参数进行非交互式执行
3. 文件传输使用 SFTP 协议
4. 支持 SSH config 中的所有主机

## 项目位置

- 源码：`/root/project/tunnel-shell/`
- Skill：`~/.hermes/skills/software-development/tunnel-shell/`
