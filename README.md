# Cyber-Persona (Python)

Simple LangGraph + WebSocket + Rich TUI demo.

## Structure

```
src/cyber_persona/
├── core/graph.py       # LangGraph workflow
├── server/ws_server.py # WebSocket server
└── client/tui.py       # Rich TUI client
```

## Quick Start

**一键启动（推荐开发用）:**
```bash
uv run python -m cyber_persona dev
```
这会同时启动 server 和 TUI，按 Ctrl+C 停止两者。

## Commands

| 命令 | 说明 |
|------|------|
| `uv run python -m cyber_persona dev` | 同时启动 server + TUI |
| `uv run python -m cyber_persona server` | 只启动 WebSocket server |
| `uv run python -m cyber_persona tui` | 只启动 TUI（需先启动 server）|

## 使用 TUI

启动后，界面类似普通 Linux 终端：

```
✓ Connected to server

>>> hello
Step B finalized: Step A processed: hello

>>> how are you
Step B finalized: Step A processed: how are you

>>> quit
✓ Goodbye!
```

输入 `quit`, `exit`, 或 `q` 退出。

## Zectrix 墨水屏插件(Google Calendar 同步)

把 Google 日历未来 30 天的事件,周期性同步成 Zectrix 墨水屏设备上的 todo。
单向同步:Google 上新增 / 修改 / 删除 / 取消的事件都会反映到设备上。

### 一次性配置

1. 在 Google Cloud Console 建一个 OAuth 2.0「桌面应用」客户端,拿到 client_id / secret
2. 在 [Zectrix 开发者后台](https://cloud.zectrix.com) 拿 API Key
3. 把以下变量填到 `.env`:

   ```dotenv
   ZECTRIX_API_KEY=...
   ZECTRIX_GOOGLE_CLIENT_ID=...
   ZECTRIX_GOOGLE_CLIENT_SECRET=...
   ZECTRIX_DEVICE_ID=          # 可选,留空会用账号下第一台
   ```

4. 跑 OAuth 授权(浏览器会打开):

   ```bash
   uv run cp zectrix auth
   ```

   token 存在 `data/zectrix/tokens/google_token.json`,自动续期。

### 日常使用

| 命令 | 用途 |
| --- | --- |
| `uv run cp zectrix sync` | 立即同步一次(调试用) |
| `uv run cp zectrix scheduler` | 前台跑定时同步,默认 12h 一次。Ctrl+C 退出 |
| `uv run cp zectrix scheduler --hours 6` | 改成 6h 一次 |
| `uv run cp zectrix scheduler --no-now` | 启动时不立即执行,等到下一个间隔 |

scheduler 是**前台进程**,关终端就停。要长期跑请自己用 `nohup` / `tmux` / `screen`:

```bash
nohup uv run cp zectrix scheduler > data/zectrix/scheduler.log 2>&1 &
```

### 数据位置

```text
data/zectrix/
├── tokens/google_token.json          # OAuth refresh token(别提交到 git)
└── synced_events/sync_state.json     # 同步状态:event_id ↔ todo_id
```

### 同步语义

每轮同步拉取未来 30 天的事件,然后:

- **新事件** → 在 Zectrix 创建一条 todo
- **现有事件改了 title / 时间 / 描述** → 更新对应 todo
- **事件从 30 天窗口消失**(被删 / 取消 / 移出窗口) → 删除对应 todo

全天事件会写 `dueDate` 但 `dueTime` 留空。

## 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest -v tests/

# 检查代码格式
uv run ruff check .
```

## Requirements

- Python 3.13+
- UV package manager
