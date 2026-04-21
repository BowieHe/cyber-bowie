import { useEffect, useRef } from "react";
import type { Message } from "@/types/events";
import { MessageBubble } from "./MessageBubble";
import { InputBox } from "./InputBox";

interface ChatProps {
  messages: Message[];
  isLoading: boolean;
  onSend: (message: string) => void;
}

export function Chat({ messages, isLoading, onSend }: ChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-screen flex-col bg-bg">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border bg-surface px-4 py-3">
        <div>
          <h1 className="text-base font-semibold">Cyber Persona</h1>
          <p className="text-xs text-text-muted">多 Agent AI 助手</p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-bg px-2.5 py-1 text-xs text-text-muted border border-border">
          <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-dot" />
          在线
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-text-muted">
            <div className="mb-3 text-4xl">🤖</div>
            <p className="text-sm">发送消息开始对话</p>
            <p className="mt-1 text-xs text-text-dim">
              你可以问任何问题，AI 会调用多个 Agent 协作回答
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <InputBox onSend={onSend} isLoading={isLoading} />
    </div>
  );
}
