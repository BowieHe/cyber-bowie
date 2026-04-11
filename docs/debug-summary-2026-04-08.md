# 调试总结 - Telegram & TUI 问题

## 问题 1: Telegram Bot 收不到消息

### 诊断结果
**根本原因：Bot Privacy Mode 开启**

检查命令：
```bash
TOKEN=$(grep MAIN_BOT_TOKEN .env | cut -d= -f2 | tr -d '"' | xargs)
curl -s "https://api.telegram.org/bot${TOKEN}/getMe" | jq .
```

返回：
```json
{
  "ok": true,
  "result": {
    "can_read_all_group_messages": false,  // <-- 问题在这里！
    ...
  }
}
```

### 解决方案（二选一）

**方案 A：禁用 Privacy Mode（推荐用于开发）**
1. 在 Telegram 中找 @BotFather
2. 发送 `/setprivacy`
3. 选择你的 bot
4. 选择 `Disable`

**方案 B：在 Group 中设置 Bot 为 Admin（推荐用于生产）**
1. 进入 Group Settings
2. Administrators → Add Administrator
3. 选择你的 bot
4. 可以只给最基本的权限

### 验证方法

1. **先测试私聊**（绕过 privacy mode）：
   - 直接给 bot 发私信
   - 检查 server 日志是否有 `[Telegram] Received message`

2. **再测试群聊**：
   - @mention bot，看是否响应
   - 如果已禁用 privacy mode 或设为 admin，不发 @ 也应该响应

---

## 问题 2: TUI 键盘输入无响应

### 诊断结果
**根本原因：stdin 不是 TTY**

验证命令：
```bash
node -e "console.log('stdin.isTTY:', process.stdin.isTTY)"
```

返回：`stdin.isTTY: undefined`

正常应该返回：`stdin.isTTY: true`

### 原因分析

当 stdin 不是 TTY 时：
- Ink 的 `useInput` hook 无法捕获单个按键
- 只能捕获完整的行输入（按 Enter 后）
- 方向键、ESC 等特殊按键无法识别

### 可能的场景

1. **通过管道运行**：`echo "test" | npm run tui`
2. **某些 CI/容器环境**：stdin 被重定向
3. **npm 脚本问题**：某些版本的 npm 会破坏 TTY
4. **WSL/Windows Terminal 问题**：终端模拟器未正确传递 TTY

### 解决方案

**方案 A：直接运行（绕过 npm）**
```bash
# 不使用 npm run
node packages/pi-tui/dist/index.js
```

**方案 B：检查终端环境**
在真实终端中运行（不是 VS Code 内置终端等）：
```bash
# 在独立终端窗口中
cd /home/bowie/code/cyber-bowie
npm run tui
```

**方案 C：使用环境变量强制 TTY**
```bash
NODE_ENV=development node packages/pi-tui/dist/index.js < /dev/tty
```

**方案 D：修改设计为只读模式**（如果必须无 TTY 运行）
如果 stdin 确实无法变成 TTY，TUI 可以作为只读监控面板：
- 自动刷新显示 sessions 和 events
- 不支持键盘导航
- 退出用 Ctrl+C

### 当前代码改动

已在 `App.tsx` 中添加：
```typescript
// 检查 stdin 是否为 TTY
const isTTY = process.stdin.isTTY;
if (isTTY && setRawMode) {
  setRawMode(true);
  setInputMode('raw');  // 支持方向键、ESC 等
} else {
  setInputMode('none'); // 只读模式
}
```

界面会根据 inputMode 显示不同的提示：
- Raw 模式：`↑↓ Navigate | s: Steering | ESC/q: Quit`
- 非 TTY 模式：`Keyboard input not available`

---

## 已添加的诊断日志

### Server 端
- `[telegram:info] Polling for updates` - 显示轮询正在进行
- `[telegram:info] Received updates { count: N }` - 显示收到消息数量
- `[shouldRespond] Checking: ...` - 显示消息过滤逻辑

### TUI 端
- `/tmp/pi-tui-debug.log` - 键盘输入日志
- 启动时记录 `stdin.isTTY` 状态

---

## 快速测试清单

### 测试 Telegram
```bash
# 1. 启动 server
npm run server

# 2. 在另一个终端检查更新
TOKEN=$(grep MAIN_BOT_TOKEN .env | cut -d= -f2 | tr -d '"' | xargs)
curl -s "https://api.telegram.org/bot${TOKEN}/getUpdates" | jq .

# 3. 给 bot 发私信，然后再次运行上面的 curl，应该能看到 update
```

### 测试 TUI
```bash
# 1. 检查 TTY
node -e "console.log('isTTY:', process.stdin.isTTY)"

# 2. 如果返回 true，运行 TUI
npm run tui

# 3. 检查日志
tail -f /tmp/pi-tui-debug.log
```

---

## 下一步行动

1. **修复 Telegram**：在 @BotFather 中禁用 privacy mode
2. **修复 TUI**：在真实 TTY 终端中运行，或使用直接 node 命令
3. **验证**：按照上面的测试清单验证修复结果

---

## 相关文件修改

| 文件 | 改动 |
|------|------|
| `packages/pi-channel-telegram/src/index.ts` | 添加轮询日志、响应判断日志 |
| `packages/pi-server/src/index.ts` | 添加消息接收日志 |
| `packages/pi-tui/src/App.tsx` | 添加 TTY 检测、input mode 显示 |
| `bots.json` | 给 bowie bot 添加 `"mode": "always"` |
