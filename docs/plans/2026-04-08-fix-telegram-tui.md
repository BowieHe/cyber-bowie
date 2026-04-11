# Fix Telegram Message Handling & TUI Input Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix two critical bugs: (1) Telegram bot not responding to messages in groups/private chats, (2) TUI keyboard input not working except ESC.

**Architecture:** The system uses a polling-based Telegram bot (pi-channel-telegram) that forwards messages to pi-server, which orchestrates persona responses. The TUI (pi-tui) uses Ink v6 + React 19 for terminal UI with keyboard input via useInput hook.

**Tech Stack:** TypeScript 6.0, Ink v6, React 19, Node.js ESM, Telegram Bot API

---

## Investigation Summary

**Current State:**
- Server starts and connects 3 bots successfully
- No message logs appear when sending messages to bot
- TUI renders but keyboard navigation (arrows, 's') doesn't work

**Root Cause Hypotheses:**
1. Telegram: Privacy mode enabled, webhook conflict, or getUpdates not receiving messages
2. TUI: Ink v6 useInput hook may have stdin handling issues or focus problems

---

## Task 1: Diagnose Telegram Message Reception

**Files:**
- Test: Direct API test via curl
- Modify: `packages/pi-channel-telegram/src/index.ts:338-360`

**Step 1: Test Telegram API directly**

Run:
```bash
# Replace with actual bot token from .env
TOKEN=$(grep MAIN_BOT_TOKEN .env | cut -d= -f2)
curl -s "https://api.telegram.org/bot${TOKEN}/getUpdates?limit=5" | jq .
```

Expected: JSON with updates array, or empty `{"ok":true,"result":[]}`

**Step 2: Check webhook status**

Run:
```bash
TOKEN=$(grep MAIN_BOT_TOKEN .env | cut -d= -f2)
curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" | jq .
```

Expected: `{"ok":true,"result":{"url":"","has_custom_certificate":false...}}`
If url is set, webhook is active and polling won't work.

**Step 3: Delete webhook if active**

Run:
```bash
TOKEN=$(grep MAIN_BOT_TOKEN .env | cut -d= -f2)
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/deleteWebhook" | jq .
```

Expected: `{"ok":true,"result":true}`

**Step 4: Add verbose polling logs to telegram channel**

Modify `packages/pi-channel-telegram/src/index.ts` inside the while loop:

```typescript
while (!stopped) {
  const controller = new AbortController();
  controllers.add(controller);

  try {
    log("info", "Polling getUpdates", { offset, personaId: config.personaId });
    const updates = await telegramRequest<TelegramApiUpdate[]>(
      bot.token,
      "getUpdates",
      {
        offset,
        timeout: pollTimeoutSeconds,
        allowed_updates: ["message"]
      },
      controller.signal
    );
    log("info", "Received updates", { count: updates.length, personaId: config.personaId });
    // ... rest of loop
```

**Step 5: Rebuild and test**

Run:
```bash
npm run build
npm run server
```

Send a message to bot in Telegram.
Expected: See "Polling getUpdates" and "Received updates" logs every 25 seconds.

---

## Task 2: Fix Telegram Privacy Mode Issue

**Files:**
- Test: Check bot status via API
- Modify: Bot settings in Telegram

**Step 1: Check if privacy mode is blocking group messages**

In Telegram:
1. Go to @BotFather
2. Send `/mybots`
3. Select your bot
4. Check "Bot Settings" → "Group Privacy"

If it says "Privacy mode is enabled for your bot", bot won't see group messages unless:
- It's an admin in the group
- User directly @mentions the bot

**Step 2: Disable privacy mode (or make bot admin)**

Option A (Recommended): Add bot as group admin
- Go to Group Settings → Administrators → Add Administrator
- Select your bot, give minimal permissions

Option B: Disable privacy mode
- In @BotFather: `/setprivacy` → Select bot → Disable

**Step 3: Test private chat first**

Send a direct message to the bot (not in group).
This bypasses privacy mode issues.

Expected: Server should log the message.

---

## Task 3: Fix TUI Input Handling

**Files:**
- Modify: `packages/pi-tui/src/App.tsx:1-100`
- Modify: `packages/pi-tui/src/index.tsx:1-8`

**Step 1: Research Ink v6 useInput issues**

Search for known issues with Ink v6 and stdin handling.
Common issues:
- Raw mode not enabled
- stdin not being properly piped
- Focus issues with Box components

**Step 2: Check if stdin is in raw mode**

Modify `packages/pi-tui/src/App.tsx`:

```typescript
import { useInput, useApp, useStdin } from 'ink';
// ...
export function App() {
  const { exit } = useApp();
  const { stdin, setRawMode } = useStdin();

  // Ensure raw mode is enabled
  useEffect(() => {
    if (setRawMode) {
      setRawMode(true);
      console.log('[TUI] Raw mode enabled');
    }
  }, [setRawMode]);

  // Debug stdin
  useEffect(() => {
    if (stdin) {
      const handler = (data: Buffer) => {
        console.log('[TUI] Raw input:', data.toString('hex'));
      };
      stdin.on('data', handler);
      return () => stdin.off('data', handler);
    }
  }, [stdin]);
```

**Step 3: Alternative - use ink's focus management**

The issue might be that no component has focus. Wrap the app in a FocusContext:

```typescript
import { FocusContext, useFocusManager } from 'ink';

function AppContent() {
  const { focusNext } = useFocusManager();

  useInput((input, key) => {
    // ... existing handler
  });

  return (
    <Box flexDirection="column" height="100%">
      {/* ... */}
    </Box>
  );
}

export function App() {
  return (
    <FocusContext.Provider value={{ activeId: 'main' }}>
      <AppContent />
    </FocusContext.Provider>
  );
}
```

**Step 4: Simplify to test basic input**

Create a minimal test file `packages/pi-tui/src/test-input.tsx`:

```typescript
import React from 'react';
import { render, Text, useInput } from 'ink';

function TestApp() {
  const [lastKey, setLastKey] = React.useState('');

  useInput((input, key) => {
    setLastKey(`input="${input}" key=${JSON.stringify(key)}`);
    if (key.escape) process.exit(0);
  });

  return <Text>Last key: {lastKey}</Text>;
}

render(<TestApp />);
```

Run:
```bash
node packages/pi-tui/dist/test-input.js
```

Press arrow keys, 's', etc.
Expected: Display updates with key info.

**Step 5: Fix App.tsx based on findings**

If minimal test works but App.tsx doesn't, the issue is likely:
- setInterval interfering with stdin
- Complex component tree blocking focus
- Missing useFocus or focusId

Add explicit focus handling:

```typescript
import { useFocus } from 'ink';

// In App component:
const { isFocused } = useFocus({ id: 'app' });

useInput((input, key) => {
  console.log('[TUI Debug] Focused:', isFocused, 'Input:', input, 'Key:', key);
  // ... rest of handler
});
```

---

## Task 4: Verify End-to-End Flow

**Files:**
- Test: Full integration test

**Step 1: Start server with debug logging**

```bash
DEBUG=telegram npm run server
```

**Step 2: Send test message to bot**

In Telegram private chat with bot:
```
Hello bot
```

Expected logs:
```
[telegram:info] Polling getUpdates {...}
[telegram:info] Received updates { count: 1, ... }
[shouldRespond] Checking: chatType=private ...
[Telegram] Received message: Hello bot...
[Orchestrator] Plan: [...]
```

**Step 3: Start TUI and verify input**

```bash
npm run tui
```

Press arrow keys, 's' key.
Expected: Navigation works, can enter steering mode.

**Step 4: Test steering in TUI**

- Navigate to active session
- Press 's' to enter steering mode
- Type a message
- Press Enter

Expected: Message appears in EventStream panel.

---

## Task 5: Clean Up Debug Code

**Files:**
- Modify: `packages/pi-channel-telegram/src/index.ts`
- Modify: `packages/pi-tui/src/App.tsx`

**Step 1: Remove verbose console.log statements**

Keep only essential logs:
- Bot connection success
- Message received (truncated)
- Response sent

**Step 2: Remove test files**

Delete `packages/pi-tui/src/test-input.tsx` if created.

**Step 3: Final build and test**

```bash
npm run build
npm run server  # Terminal 1
npm run tui     # Terminal 2
```

Verify both features work correctly.

---

## Testing Checklist

- [ ] Telegram private chat messages are received and responded to
- [ ] Telegram group messages (with bot as admin) are received
- [ ] TUI arrow keys navigate session list
- [ ] TUI 's' key enters steering mode
- [ ] TUI ESC/q quits
- [ ] TUI steering input can be submitted
- [ ] Server logs show complete message flow

---

## References

- @superpowers:systematic-debugging - For debugging approach
- @superpowers:executing-plans - For task execution
- Ink v6 docs: https://github.com/vadimdemedes/ink
- Telegram Bot API: https://core.telegram.org/bots/api
