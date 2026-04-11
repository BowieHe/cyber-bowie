# Cyber Persona 新架构设计

## 当前问题

现有代码结构混杂，职责不清晰：

1. **core/graph.py** - 混合了 LLM 配置、节点定义、图构建
2. **server/ws_server.py** - 混合了 FastAPI 应用、路由处理、业务逻辑
3. **client/tui.py** - 混合了 UI 渲染、HTTP 请求、状态管理
4. 缺少配置集中管理
5. 缺少 persona/skill 系统（原 TS 版本的核心功能）

## 新架构设计

采用分层架构，每层职责单一：

```
cyber_persona/
├── config/              # 配置层
│   ├── __init__.py
│   ├── settings.py      # 环境变量、全局配置
│   └── loader.py        # 配置文件加载 (personas.json, SOUL.md)
│
├── core/                # 核心领域层
│   ├── __init__.py
│   ├── models.py        # 数据模型 (Message, Persona, Session)
│   ├── events.py        # 事件/流类型定义
│   └── types.py         # 类型别名、枚举
│
├── engine/              # 执行引擎层
│   ├── __init__.py
│   ├── builder.py       # Graph 构建器
│   ├── state.py         # 状态管理 (GraphState)
│   ├── nodes/           # 节点实现
│   │   ├── __init__.py
│   │   ├── input.py     # 输入处理节点
│   │   ├── llm.py       # LLM 调用节点
│   │   ├── output.py    # 输出格式化节点
│   │   └── persona.py   # Persona 路由节点
│   └── edges.py         # 边逻辑/条件路由
│
├── persona/             # 人格系统
│   ├── __init__.py
│   ├── models.py        # Persona 领域模型
│   ├── loader.py        # SOUL.md / souls/*.md 加载器
│   ├── registry.py      # Persona 注册表
│   ├── context.py       # 上下文构建
│   └── team.py          # 团队协作逻辑
│
├── skills/              # 技能系统
│   ├── __init__.py
│   ├── base.py          # Skill 抽象基类
│   ├── registry.py      # 技能注册表
│   ├── manager.py       # 技能生命周期管理
│   └── built_in/        # 内置技能
│       ├── __init__.py
│       ├── superpower.py    # 抓重点技能
│       └── search.py        # 搜索技能 (MCP)
│
├── channels/            # 接入渠道层
│   ├── __init__.py
│   ├── base.py          # Channel 抽象基类
│   ├── models.py        # 渠道消息模型
│   ├── websocket.py     # WebSocket 渠道
│   └── telegram.py      # Telegram 渠道
│
├── server/              # HTTP/WebSocket 服务层
│   ├── __init__.py
│   ├── app.py           # FastAPI 应用工厂
│   ├── deps.py          # 依赖注入
│   ├── routes/          # API 路由
│   │   ├── __init__.py
│   │   ├── health.py    # 健康检查
│   │   ├── chat.py      # 聊天接口
│   │   ├── skills.py    # 技能列表
│   │   └── personas.py  # Persona 管理
│   └── middleware/      # 中间件
│       ├── __init__.py
│       ├── cors.py      # CORS 配置
│       └── logging.py   # 请求日志
│
├── client/              # 客户端层
│   ├── __init__.py
│   ├── base.py          # 客户端基类
│   ├── api.py           # API 客户端封装
│   ├── ui/              # UI 组件
│   │   ├── __init__.py
│   │   ├── base.py      # UI 基类
│   │   ├── tui.py       # 终端 UI (Rich)
│   │   └── web.py       # Web UI 组件
│   └── cli.py           # CLI 命令处理
│
├── utils/               # 工具层
│   ├── __init__.py
│   ├── logging.py       # 日志配置
│   └── helpers.py       # 通用工具函数
│
└── __main__.py          # 入口点
```

## 层间依赖关系

```
client/
    ↓ (HTTP/WebSocket)
server/
    ↓ (调用)
channels/ → engine/ → skills/
                ↓
            persona/
                ↓
            core/ ← config/
```

- **上层依赖下层**，下层不依赖上层
- **同层之间**通过事件或接口通信
- **core** 是最底层，定义基础模型

## 数据流向

```
用户输入 → Channel → Server → Engine → Persona → Skills → LLM
                                              ↓
响应 ← Channel ← Server ← Engine ← Output formatting
```

## 关键设计原则

1. **单一职责**：每个模块只做一件事
2. **依赖注入**：通过构造函数注入依赖，便于测试
3. **接口隔离**：定义清晰的抽象基类
4. **配置集中**：所有配置统一管理
5. **插件化**：Skills 和 Channels 可插拔

## 迁移计划

1. 创建新的目录结构
2. 迁移配置层 (config)
3. 迁移核心领域层 (core)
4. 迁移引擎层 (engine)
5. 实现 persona 系统
6. 实现 skill 系统
7. 重构 server 层
8. 重构 client 层
9. 更新入口文件
10. 测试验证
