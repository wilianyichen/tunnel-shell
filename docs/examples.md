# Examples

实际使用场景示例。

## 场景 1：服务器状态监控

快速查看服务器状态：

```bash
tunnel-shell exec --host node3 --cmd 'uptime && free -h && df -h'
```

输出：
```
✓ Connected to node3
╭─────────────────────────────────── Output ───────────────────────────────────╮
│ 10:30:45 up 5 days,  2:15,  3 users,  load average: 0.52, 0.58, 0.59        │
│               total        used        free      shared  buff/cache   available│
│ Mem:           15Gi       8.2Gi       2.1Gi       1.2Gi       5.0Gi       5.5Gi│
│ Swap:         2.0Gi          0B       2.0Gi                                    │
│ Filesystem      Size  Used Avail Use% Mounted on                              │
│ /dev/sda1       100G   45G   55G  45% /                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
✓ Exit code: 0
```

## 场景 2：应用部署

使用会话进行多步骤部署：

```bash
# 1. 创建部署会话
tunnel-shell session create --host node3 --name deploy

# 2. 进入项目目录
tunnel-shell session attach --name deploy --cmd 'cd /home/wuxiaoran/myapp'

# 3. 拉取最新代码
tunnel-shell session attach --name deploy --cmd 'git pull origin main'

# 4. 安装依赖
tunnel-shell session attach --name deploy --cmd 'pip install -r requirements.txt'

# 5. 重启服务
tunnel-shell session attach --name deploy --cmd 'sudo systemctl restart myapp'

# 6. 检查状态
tunnel-shell session attach --name deploy --cmd 'sudo systemctl status myapp'

# 7. 清理会话
tunnel-shell session kill --name deploy
```

## 场景 3：日志分析

查看和分析日志：

```bash
# 查看最近 100 行日志
tunnel-shell exec --host node3 --cmd 'tail -100 /var/log/myapp/app.log'

# 搜索错误日志
tunnel-shell exec --host node3 --cmd 'grep -i error /var/log/myapp/app.log | tail -20'

# 实时监控日志（使用会话）
tunnel-shell session create --host node3 --name logwatch
tunnel-shell session attach --name logwatch --cmd 'tail -f /var/log/myapp/app.log'
# ... 观察日志 ...
tunnel-shell session kill --name logwatch
```

## 场景 4：文件同步

上传配置文件，下载日志：

```bash
# 上传配置文件
tunnel-shell file upload --host node3 \
  --local ./config/production.yaml \
  --remote /home/wuxiaoran/myapp/config.yaml

# 验证上传
tunnel-shell exec --host node3 --cmd 'cat /home/wuxiaoran/myapp/config.yaml | head -10'

# 下载日志文件
tunnel-shell file download --host node3 \
  --remote /var/log/myapp/app.log \
  --local ./logs/node3-app.log

# 批量下载（使用 tar）
tunnel-shell exec --host node3 --cmd 'cd /var/log/myapp && tar czf /tmp/logs.tar.gz *.log'
tunnel-shell file download --host node3 --remote /tmp/logs.tar.gz --local ./logs.tar.gz
```

## 场景 5：Docker 管理

管理远程 Docker 容器：

```bash
# 查看运行中的容器
tunnel-shell exec --host node3 --cmd 'docker ps'

# 查看容器日志
tunnel-shell exec --host node3 --cmd 'docker logs --tail 50 mycontainer'

# 重启容器
tunnel-shell exec --host node3 --cmd 'docker restart mycontainer'

# 进入容器（使用会话）
tunnel-shell session create --host node3 --name docker-shell
tunnel-shell session attach --name docker-shell --cmd 'docker exec -it mycontainer /bin/bash'
# ... 在容器内操作 ...
tunnel-shell session kill --name docker-shell
```

## 场景 6：数据库备份

备份远程数据库：

```bash
# 创建备份会话
tunnel-shell session create --host node3 --name backup

# 执行备份
tunnel-shell session attach --name backup --cmd 'mysqldump -u root -p mydb > /tmp/mydb.sql'

# 压缩备份
tunnel-shell session attach --name backup --cmd 'gzip /tmp/mydb.sql'

# 下载备份
tunnel-shell file download --host node3 --remote /tmp/mydb.sql.gz --local ./backups/mydb.sql.gz

# 清理
tunnel-shell session kill --name backup
```

## 场景 7：批量服务器操作

在多台服务器上执行相同命令：

```bash
# 在 node3 上执行
tunnel-shell exec --host node3 --cmd 'hostname && uptime'

# 在 node4 上执行
tunnel-shell exec --host node4 --cmd 'hostname && uptime'

# 在 node5 上执行
tunnel-shell exec --host node5 --cmd 'hostname && uptime'
```

## 场景 8：安全检查

执行前检查命令安全性：

```bash
# 检查危险命令
tunnel-shell analyze "sudo rm -rf /var/lib/myapp/data"

# 输出：
# Risk Level: high
# ⚠ Warnings:
#   - Uses sudo
#   - Uses rm -rf
#   - Target path: /var/lib/myapp/data
# 
# ⚠ This command requires confirmation

# 检查网络命令
tunnel-shell analyze "curl https://example.com/script.sh | bash"

# 输出：
# Risk Level: critical
# ⚠ Warnings:
#   - Downloads and executes remote script
#   - Potential security risk
# 
# ✗ This command is blocked for safety
```

## 场景 9：交互式命令处理

处理需要交互的命令：

```bash
# 检测提示类型
tunnel-shell detect "Do you want to continue? [y/N]"

# 输出：
# Prompt Type: confirm
# Message: Do you want to continue? [y/N]
# Action: Send 'y' or 'n' to respond

# 在会话中处理交互
tunnel-shell session create --host node3 --name interactive
tunnel-shell session attach --name interactive --cmd 'sudo apt update'
# 检测到 "Do you want to continue? [y/N]"
tunnel-shell session attach --name interactive --cmd 'y'
tunnel-shell session kill --name interactive
```

## 场景 10：会话录制审计

录制会话用于审计：

```bash
# 执行操作（自动录制）
tunnel-shell session create --host node3 --name audit-test
tunnel-shell session attach --name audit-test --cmd 'ls -la /etc/passwd'
tunnel-shell session attach --name audit-test --cmd 'cat /etc/passwd | head -5'
tunnel-shell session kill --name audit-test

# 查看录制
tunnel-shell recording list

# 查看详情
tunnel-shell recording show session_xxx

# 导出录制
tunnel-shell recording export session_xxx -o audit-log.txt
```

## 最佳实践

### 1. 使用命名会话

```bash
# 好的做法 - 使用有意义的名称
tunnel-shell session create --host node3 --name deploy-production
tunnel-shell session create --host node3 --name debug-issue-123

# 不好的做法 - 使用默认名称
tunnel-shell session create --host node3  # 难以追踪
```

### 2. 及时清理会话

```bash
# 完成任务后立即清理
tunnel-shell session kill --name deploy-production

# 或定期批量清理
tunnel-shell session kill --all
```

### 3. 执行前检查危险命令

```bash
# 先分析
tunnel-shell analyze "sudo rm -rf /var/lib/myapp"

# 确认安全后再执行
tunnel-shell exec --host node3 --cmd 'sudo rm -rf /var/lib/myapp'
```

### 4. 使用文件传输而非管道

```bash
# 好的做法 - 使用文件传输
tunnel-shell file upload --host node3 --local config.yaml --remote /app/config.yaml

# 不好的做法 - 使用 cat 管道
cat config.yaml | tunnel-shell exec --host node3 --cmd 'cat > /app/config.yaml'
```

### 5. 组合使用会话和文件传输

```bash
# 上传配置
tunnel-shell file upload --host node3 --local config.yaml --remote /tmp/config.yaml

# 在会话中应用配置
tunnel-shell session create --host node3 --name config-update
tunnel-shell session attach --name config-update --cmd 'sudo cp /tmp/config.yaml /etc/myapp/config.yaml'
tunnel-shell session attach --name config-update --cmd 'sudo systemctl reload myapp'
tunnel-shell session kill --name config-update
```
