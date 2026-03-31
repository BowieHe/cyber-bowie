export interface ClawbotInboundMessage {
  channel: "clawbot";
  sessionId: string;
  userId: string;
  text: string;
  raw: unknown;
}

export interface ClawbotOutboundMessage {
  reply: string;
  sessionId: string;
  userId: string;
}

function pickFirstString(values: unknown[]): string | undefined {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return undefined;
}

export function parseClawbotInbound(payload: unknown): ClawbotInboundMessage | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const record = payload as Record<string, unknown>;
  const message = record.message && typeof record.message === "object"
    ? (record.message as Record<string, unknown>)
    : null;
  const user = record.user && typeof record.user === "object"
    ? (record.user as Record<string, unknown>)
    : null;
  const session = record.session && typeof record.session === "object"
    ? (record.session as Record<string, unknown>)
    : null;

  const text = pickFirstString([
    record.text,
    record.content,
    message?.text,
    message?.content,
    record.prompt
  ]);
  const userId = pickFirstString([
    record.userId,
    record.fromUserId,
    record.from,
    user?.id,
    user?.userId,
    record.sender
  ]);
  const sessionId = pickFirstString([
    record.sessionId,
    record.conversationId,
    record.chatId,
    session?.id,
    userId
  ]);

  if (!text || !userId || !sessionId) {
    return null;
  }

  return {
    channel: "clawbot",
    sessionId,
    userId,
    text,
    raw: payload
  };
}

export function buildClawbotOutbound(
  inbound: ClawbotInboundMessage,
  reply: string
): ClawbotOutboundMessage {
  return {
    reply,
    sessionId: inbound.sessionId,
    userId: inbound.userId
  };
}
