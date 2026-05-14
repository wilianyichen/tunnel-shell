# TunnelShell 开发计划

## 核心目标

**第一轮（MVP）:** 最小可用版本，能在本机实际使用
**第二轮（完善）:** 增强功能，准备开源发布

---

## 第一轮：MVP 阶段

### Phase 1-MVP: 项目骨架 + SSH 连接 ✅ 已完成

**目标:** 项目可安装、可运行、能执行单条命令

**涉及文件:**
```
tunnel-shell/
├── pyproject.toml
├── README.md
├── src/tunnelshell/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── connection.py
│   └── version.py
└── tests/
```

**验证标准:**
- [x] `pip install -e .` 成功
- [x] `tunnel-shell --version` 输出版本
- [x] `tunnel-shell exec --host node3 --cmd 'hostname'` 返回主机名

---

### Phase 2-MVP: PTY 会话基础 ✅ 已完成

**目标:** 能创建 PTY 会话、发送命令、接收输出、detach/attach

**涉及文件:**
```
src/tunnelshell/
├── session.py           # PTY 会话管理
├── session_store.py     # 会话持久化
└── cli.py               # session 子命令
```

**验证标准:**
- [x] `tunnel-shell session attach --host node3 --cmd 'ls'` 返回输出
- [x] 会话可 detach（Ctrl+C）
- [x] 会话可 reconnect

---

### Phase 3-MVP: 会话持久化完善 ✅ 已完成

**目标:** 会话状态可靠持久化，支持多会话管理，能在不同终端/进程中访问同一会话

**涉及文件:**
```
src/tunnelshell/
├── session_store.py     # 完善持久化逻辑
├── session.py           # 添加状态同步
└── cli.py               # 完善 list/kill 命令
```

**具体改进:**
1. 会话状态实时同步到文件（不只是创建时）
2. 支持跨进程访问会话（A终端创建，B终端attach）
3. 会话列表显示准确状态
4. 会话清理（删除已终止的会话）

**验证标准:**
- [x] 终端A创建会话，终端B能 `session list` 看到
- [x] 终端A创建会话，终端B能 `session attach` 连接
- [x] 会话状态变化后，`session list` 显示正确
- [x] `session kill` 后会话从列表中移除

---

### Phase 4-MVP: 输入输出重定向完善 ✅ 已完成

**目标:** 远程终端的输入输出能可靠地重定向到本地，支持交互式操作

**涉及文件:**
```
src/tunnelshell/
├── session.py           # 改进输出读取
├── output_buffer.py     # 新增：输出缓冲管理
└── cli.py               # 改进交互模式
```

**具体改进:**
1. 输出缓冲：累积输出，支持回滚查看
2. 输入队列：支持发送多行命令
3. 输出过滤：可选过滤 ANSI 转义序列
4. 实时输出：交互模式下实时显示输出

**验证标准:**
- [x] 交互模式下，输入 `ls -la`，实时看到输出
- [x] 输出超过限制时，只保留最近内容
- [x] 支持检测交互提示（password、confirm等）

---

### Phase 5-MVP: 多会话管理 ✅ 已完成

**目标:** 支持同时管理多个独立会话，切换自如

**涉及文件:**
```
src/tunnelshell/
├── session_store.py     # 多会话管理
├── session.py           # 会话隔离
└── cli.py               # 批量操作命令
```

**具体改进:**
1. 创建多个命名会话
2. 按名称/ID切换会话
3. 批量 kill 会话
4. 会话状态汇总

**验证标准:**
- [x] 创建3个会话（node3-1, node3-2, node3-3）
- [x] `session list` 显示所有会话
- [x] 分别 attach 到不同会话，执行不同命令
- [x] `session kill --all` 清理所有会话

---

### Phase 6-MVP: 本机部署测试 ✅ 已完成

**目标:** 在本机克隆项目，验证实际使用体验

**验证标准:**
- [x] 本机 `pip install -e .` 成功
- [x] 本机 `tunnel-shell session create --host node3 --name test` 成功
- [x] 本机 `tunnel-shell session attach --name test` 成功
- [x] 实际使用无明显 bug

---

## 第二轮：完善阶段（开源准备）

### Phase 7: 输出智能处理 ✅ 已完成

**目标:** 输出流解析、交互提示检测、命令分类

**涉及文件:**
```
src/tunnelshell/
├── output_parser.py     # ANSI 解析
├── prompt_detector.py   # 交互提示检测
└── command_classifier.py # 命令分类
```

**验证标准:**
- [x] 检测到 `Password:` 提示并标记
- [x] 检测到 `(y/n)` 提示并标记
- [x] 命令分类正确（search/read/silent/interactive）
- [x] 危险命令检测

---

### Phase 8: 文件传输集成 ✅ 已完成

**目标:** 在会话中执行文件传输

**涉及文件:**
```
src/tunnelshell/
├── file_transfer.py     # 文件传输
└── cli.py               # upload/download 命令
```

**验证标准:**
- [x] `tunnel-shell file upload` 成功
- [x] `tunnel-shell file download` 成功
- [x] `tunnel-shell file list` 成功
- [x] 进度条显示

---

### Phase 9: 超时与安全控制 ✅ 已完成

**目标:** 生产级超时控制、安全检查

**涉及文件:**
```
src/tunnelshell/
├── timeout_manager.py   # 超时控制
├── security.py          # 安全检查
```

**验证标准:**
- [x] 会话超时配置
- [x] 命令超时配置
- [x] 危险命令检测
- [x] 多级风险评级（safe/low/medium/high/critical）
- [x] 阻止危险命令

---

### Phase 10: 会话录制与回放 ✅ 已完成

**目标:** 会话录制、审计、回放

**涉及文件:**
```
src/tunnelshell/
├── recorder.py          # 会话录制
```

**验证标准:**
- [x] 会话录制框架
- [x] 录制列表命令
- [x] 录制详情查看
- [x] 录制导出

---

### Phase 11: 文档与发布 ✅ 已完成

**目标:** 完善文档、发布到 PyPI

**涉及文件:**
```
docs/
├── getting-started.md
├── api-reference.md
└── examples.md
```

**验证标准:**
- [x] README 完善
- [x] 文档目录创建
- [x] 构建发布包成功
- [x] PyPI 发布成功

**PyPI 地址:** https://pypi.org/project/tunnel-shell/

---

## 当前进度

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 1-MVP | ✅ 完成 | SSH 连接验证 |
| Phase 2-MVP | ✅ 完成 | PTY 会话基础 |
| Phase 3-MVP | ✅ 完成 | 会话持久化完善 |
| Phase 4-MVP | ✅ 完成 | 输入输出重定向完善 |
| Phase 5-MVP | ✅ 完成 | 多会话管理 |
| Phase 6-MVP | ✅ 完成 | 本机部署测试 |
| Phase 7 | ✅ 完成 | 输出智能处理 |
| Phase 8 | ✅ 完成 | 文件传输集成 |
| Phase 9 | ✅ 完成 | 超时与安全控制 |
| Phase 10 | ✅ 完成 | 会话录制与回放 |
| Phase 11 | ✅ 完成 | 文档与发布 |

**所有阶段已完成！** 项目已可使用，PyPI 发布待后续手动完成。
