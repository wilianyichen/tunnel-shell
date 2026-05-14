# TunnelShell 优化计划 v2.0

## 项目现状

**已完成：** 11 个阶段，核心功能完整，已发布 PyPI
**代码量：** 2684 行，15 个模块
**测试：** 1 个基础测试文件
**文档：** 基础文档完整

---

## 优化目标

将 TunnelShell 从可用工具升级为生产级项目：
1. 测试覆盖率 > 80%
2. 完善错误处理和用户体验
3. 添加异步支持提升性能
4. MCP Server 模式支持 AI 集成
5. 完善文档和开发体验

---

## Phase 12: 测试覆盖（高优先级）

**目标：** 测试覆盖率 > 80%

### 12.1 单元测试

**涉及文件：** `tests/` 目录

**Worker 任务：**
- Worker A: `tests/test_config.py` - SSHConfig, HostConfig 测试
- Worker B: `tests/test_connection.py` - Connection 类测试（mock SSH）
- Worker C: `tests/test_session.py` - PTYSession 测试（mock channel）
- Worker D: `tests/test_output_buffer.py` - OutputBuffer 测试

**验证标准：**
- [ ] `pytest tests/` 全部通过
- [ ] 覆盖率 > 80%

### 12.2 集成测试

**涉及文件：** `tests/integration/`

**Worker 任务：**
- Worker A: `tests/integration/test_session_workflow.py` - 完整会话流程
- Worker B: `tests/integration/test_file_transfer.py` - 文件传输流程

**验证标准：**
- [ ] 集成测试通过
- [ ] 真实 SSH 连接测试（可选）

### 12.3 CI/CD 配置

**涉及文件：** `.github/workflows/`

**Worker 任务：**
- Worker: `.github/workflows/test.yml` - 自动测试流程

**验证标准：**
- [ ] GitHub Actions 配置完成

---

## Phase 13: 错误处理增强（高优先级）

**目标：** 更友好的错误消息和自动恢复

### 13.1 异常体系重构

**涉及文件：** `src/tunnelshell/exceptions.py`（新建）

**Worker 任务：**
- Worker: 创建统一的异常类层次

**文件内容：**
```python
class TunnelShellError(Exception): ...
class ConnectionError(TunnelShellError): ...
class AuthenticationError(ConnectionError): ...
class SessionError(TunnelShellError): ...
class TimeoutError(SessionError): ...
class CommandError(TunnelShellError): ...
```

### 13.2 错误消息优化

**涉及文件：** 各模块错误处理

**Worker 任务：**
- Worker A: `connection.py` - 连接错误优化
- Worker B: `session.py` - 会话错误优化
- Worker C: `cli.py` - CLI 错误展示优化

**验证标准：**
- [ ] 错误消息清晰友好
- [ ] 包含解决建议

### 13.3 自动重试机制

**涉及文件：** `src/tunnelshell/retry.py`（新建）

**Worker 任务：**
- Worker: 实现连接重试逻辑

**验证标准：**
- [ ] 连接失败自动重试
- [ ] 可配置重试次数和间隔

---

## Phase 14: 性能优化（中优先级）

**目标：** 异步支持，提升并发性能

### 14.1 异步连接层

**涉及文件：** `src/tunnelshell/async_connection.py`（新建）

**Worker 任务：**
- Worker: 使用 asyncssh 实现异步连接

**依赖：** `pip install asyncssh`

**验证标准：**
- [ ] 异步连接可用
- [ ] 性能对比测试

### 14.2 异步会话管理

**涉及文件：** `src/tunnelshell/async_session.py`（新建）

**Worker 任务：**
- Worker: 异步 PTY 会话实现

**验证标准：**
- [ ] 异步会话可用
- [ ] 支持并发会话

### 14.3 连接池

**涉及文件：** `src/tunnelshell/pool.py`（新建）

**Worker 任务：**
- Worker: SSH 连接池实现

**验证标准：**
- [ ] 连接复用
- [ ] 自动清理空闲连接

---

## Phase 15: MCP Server 模式（中优先级）

**目标：** 让其他 AI 工具可以调用 TunnelShell

### 15.1 MCP Server 实现

**涉及文件：** `src/tunnelshell/mcp_server.py`（新建）

**Worker 任务：**
- Worker: 实现 MCP Server

**工具定义：**
- `ssh_exec` - 执行命令
- `ssh_session_create` - 创建会话
- `ssh_session_attach` - 连接会话
- `ssh_file_upload` - 上传文件
- `ssh_file_download` - 下载文件

**验证标准：**
- [ ] MCP Server 可启动
- [ ] Claude Desktop 可调用

### 15.2 MCP 配置示例

**涉及文件：** `docs/mcp-setup.md`（新建）

**Worker 任务：**
- Worker: 编写 MCP 配置文档

**验证标准：**
- [ ] 配置文档完整

---

## Phase 16: 功能增强（中优先级）

### 16.1 交互模式改进

**涉及文件：** `src/tunnelshell/interactive.py`（新建）

**Worker 任务：**
- Worker: 实现真正的交互式终端

**验证标准：**
- [ ] 支持实时输入输出
- [ ] 支持 Ctrl+C 中断

### 16.2 端口转发

**涉及文件：** `src/tunnelshell/forward.py`（新建）

**Worker 任务：**
- Worker: 实现本地/远程端口转发

**验证标准：**
- [ ] 本地端口转发可用
- [ ] 远程端口转发可用

### 16.3 配置文件支持

**涉及文件：** `src/tunnelshell/config_loader.py`（新建）

**Worker 任务：**
- Worker: 实现 YAML 配置加载

**配置文件：** `~/.tunnelshell/config.yaml`

**验证标准：**
- [ ] 配置文件加载成功
- [ ] 支持默认配置

---

## Phase 17: 文档完善（低优先级）

### 17.1 架构文档

**涉及文件：** `docs/architecture.md`（新建）

**Worker 任务：**
- Worker: 编写架构设计文档

### 17.2 贡献指南

**涉及文件：** `CONTRIBUTING.md`（新建）

**Worker 任务：**
- Worker: 编写贡献指南

### 17.3 英文文档

**涉及文件：** `README.en.md`（新建）

**Worker 任务：**
- Worker: 翻译英文文档

---

## Phase 18: 开发体验（低优先级）

### 18.1 代码质量工具

**涉及文件：** `.pre-commit-config.yaml`（新建）

**Worker 任务：**
- Worker: 配置 pre-commit hooks

### 18.2 性能基准

**涉及文件：** `benchmarks/`（新建）

**Worker 任务：**
- Worker: 编写性能基准测试

---

## 多 Agent 协作模式

### 主 Agent（Orchestrator）

**职责：**
- 架构判断和技术选型
- 任务分解和分配
- 集成和最终验证
- 处理跨模块问题

### Explorer（只读调查）

**职责：**
- 调研竞品实现
- 分析现有代码
- 生成技术报告
- 不修改任何代码

### Worker（边界明确的实现）

**职责：**
- 实现明确指定的功能
- 只修改分配的文件
- 编写对应测试
- 不跨模块修改

**规则：**
- 一个 Worker 只负责一组相关文件
- 不同 Worker 不修改同一批文件
- Worker 完成后报告结果，不自行集成

---

## 实施顺序

| Phase | 优先级 | 预计时间 | Agent 模式 |
|-------|--------|----------|------------|
| 12. 测试覆盖 | 🔴 高 | 2-3 天 | 主 Agent + 4 Workers |
| 13. 错误处理 | 🔴 高 | 1-2 天 | 主 Agent + 3 Workers |
| 14. 性能优化 | 🟡 中 | 3-5 天 | 主 Agent + 3 Workers |
| 15. MCP Server | 🟡 中 | 2-3 天 | 主 Agent + 2 Workers |
| 16. 功能增强 | 🟡 中 | 按需 | 主 Agent + 3 Workers |
| 17. 文档完善 | 🟢 低 | 1 天 | 主 Agent + 3 Workers |
| 18. 开发体验 | 🟢 低 | 1-2 天 | 主 Agent + 2 Workers |

---

## 文件修改清单

### 新建文件

```
tests/
├── test_config.py
├── test_connection.py
├── test_session.py
├── test_output_buffer.py
├── integration/
│   ├── test_session_workflow.py
│   └── test_file_transfer.py

src/tunnelshell/
├── exceptions.py
├── retry.py
├── async_connection.py
├── async_session.py
├── pool.py
├── mcp_server.py
├── interactive.py
├── forward.py
└── config_loader.py

docs/
├── architecture.md
├── mcp-setup.md
└── README.en.md

.github/workflows/
└── test.yml

benchmarks/
└── bench_session.py

CONTRIBUTING.md
.pre-commit-config.yaml
```

### 修改文件

```
src/tunnelshell/
├── connection.py  # 错误处理优化
├── session.py     # 错误处理优化
└── cli.py         # 错误展示优化
```

---

## 验证标准

### Phase 12 完成
- [ ] `pytest tests/` 全部通过
- [ ] 覆盖率报告生成
- [ ] GitHub Actions 运行成功

### Phase 13 完成
- [ ] 错误消息清晰友好
- [ ] 自动重试工作正常
- [ ] 异常类层次完整

### Phase 14 完成
- [ ] 异步 API 可用
- [ ] 性能提升明显
- [ ] 连接池工作正常

### Phase 15 完成
- [ ] MCP Server 可启动
- [ ] Claude Desktop 可调用
- [ ] 文档完整

### Phase 16 完成
- [ ] 交互模式流畅
- [ ] 端口转发可用
- [ ] 配置文件加载成功

---

## 下一步

开始 Phase 12: 测试覆盖

**任务分配：**
- Worker A: `tests/test_config.py`
- Worker B: `tests/test_connection.py`
- Worker C: `tests/test_session.py`
- Worker D: `tests/test_output_buffer.py`

是否开始执行？
