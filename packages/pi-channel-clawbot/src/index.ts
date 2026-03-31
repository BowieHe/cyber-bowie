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
  text?: string;
  content?: string;
  message?: {
    role: "assistant";
    content: string;
  };
}

function pickFirstString(values: unknown[]): string | undefined {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return undefined;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

function pickFromRecord(record: Record<string, unknown> | null, keys: string[]): string | undefined {
  if (!record) {
    return undefined;
  }

  return pickFirstString(keys.map((key) => record[key]));
}

export function parseClawbotInbound(payload: unknown): ClawbotInboundMessage | null {
  const record = asRecord(payload);

  if (!record) {
    return null;
  }

  const message = asRecord(record.message);
  const user = asRecord(record.user);
  const session = asRecord(record.session);
  const event = asRecord(record.event);
  const data = asRecord(record.data);
  const sender = asRecord(record.sender);
  const conversation = asRecord(record.conversation);

  const text = pickFirstString([
    record.text,
    record.content,
    record.body,
    record.question,
    record.query,
    message?.text,
    message?.content,
    message?.body,
    event?.text,
    event?.content,
    data?.text,
    data?.content,
    record.prompt
  ]);
  const userId = pickFirstString([
    record.userId,
    record.fromUserId,
    record.from,
    record.openid,
    record.uid,
    user?.id,
    user?.userId,
    user?.openid,
    sender?.id,
    sender?.userId,
    sender?.openid,
    event?.userId,
    data?.userId,
    record.sender
  ]);
  const sessionId = pickFirstString([
    record.sessionId,
    record.conversationId,
    record.chatId,
    record.roomId,
    record.threadId,
    session?.id,
    conversation?.id,
    event?.sessionId,
    event?.conversationId,
    data?.sessionId,
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
    userId: inbound.userId,
    text: reply,
    content: reply,
    message: {
      role: "assistant",
      content: reply
    }
  };
}
