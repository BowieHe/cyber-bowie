import { AlertCircle } from "lucide-react";
import type { Message } from "@/types/events";
import { MarkdownRender } from "./MarkdownRender";
import { ThinkingBlock } from "./ThinkingBlock";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-user-bg text-white rounded-br-sm"
            : "bg-ai-bg border border-border rounded-bl-sm"
        }`}
      >
        {!isUser && message.thinking.length > 0 && (
          <ThinkingBlock thinking={message.thinking} isLoading={message.isLoading} />
        )}

        {message.content ? (
          <MarkdownRender content={message.content} />
        ) : message.isLoading ? (
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <div className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse-dot" />
            生成中...
          </div>
        ) : null}

        {message.error && (
          <div className="mt-2 flex items-center gap-1.5 rounded-md bg-danger/10 px-2.5 py-1.5 text-xs text-danger">
            <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            {message.error}
          </div>
        )}
      </div>
    </div>
  );
}
