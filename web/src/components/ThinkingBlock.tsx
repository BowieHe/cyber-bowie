import { useState } from "react";
import { ChevronDown, Loader2 } from "lucide-react";

interface ThinkingBlockProps {
  thinking: string[];
  isLoading: boolean;
}

export function ThinkingBlock({ thinking, isLoading }: ThinkingBlockProps) {
  const [expanded, setExpanded] = useState(false);

  const hasContent = thinking.length > 0;
  if (!hasContent && !isLoading) return null;

  return (
    <div className="mb-2 rounded-lg border border-border/60 bg-surface/50 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-3 py-1.5 text-left hover:bg-surface-hover transition-colors"
      >
        <div className="flex items-center gap-2">
          {isLoading && (
            <Loader2 className="h-3 w-3 animate-spin text-accent" />
          )}
          <span className="text-xs font-medium text-text-muted">
            {isLoading ? "Thinking..." : "Thought process"}
          </span>
        </div>
        <ChevronDown
          className={`h-3.5 w-3.5 text-text-dim transition-transform ${expanded ? "rotate-180" : ""}`}
        />
      </button>

      {expanded && hasContent && (
        <div className="px-3 pb-2 border-t border-border/40 space-y-2">
          {thinking.map((text, i) => (
            <p key={i} className="text-xs text-text-muted leading-relaxed whitespace-pre-wrap">
              {text}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
