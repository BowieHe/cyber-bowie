import { useState } from "react";
import { Check, ChevronDown, Loader2, X } from "lucide-react";
import type { NodeInfo } from "@/types/events";
import { NODE_NAME_MAP } from "@/types/events";

interface TimelineNodeProps {
  node: NodeInfo;
  isLast: boolean;
}

export function TimelineNode({ node, isLast }: TimelineNodeProps) {
  const [expanded, setExpanded] = useState(false);
  const displayName = NODE_NAME_MAP[node.name] || node.name;

  const icon =
    node.status === "running" ? (
      <Loader2 className="h-4 w-4 animate-spin text-accent" />
    ) : node.status === "error" ? (
      <X className="h-4 w-4 text-danger" />
    ) : (
      <Check className="h-4 w-4 text-success" />
    );

  const duration =
    node.endTime && node.startTime
      ? ((node.endTime - node.startTime) / 1000).toFixed(1)
      : null;

  return (
    <div className="flex gap-3">
      {/* Timeline line */}
      <div className="flex flex-col items-center">
        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-surface border border-border">
          {icon}
        </div>
        {!isLast && (
          <div className="mt-1 h-full w-px bg-border min-h-[1.5rem]" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{displayName}</span>
          {node.status === "running" && (
            <span className="text-xs text-accent animate-pulse-dot">运行中</span>
          )}
          {duration && (
            <span className="text-xs text-text-dim">{duration}s</span>
          )}
        </div>

        {node.statusMessage && (
          <p className="mt-0.5 text-xs text-text-muted line-clamp-1">
            {node.statusMessage}
          </p>
        )}

        {node.output && node.output.length > 100 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-1 flex items-center gap-0.5 text-xs text-text-dim hover:text-text transition-colors"
          >
            <ChevronDown
              className={`h-3 w-3 transition-transform ${expanded ? "rotate-180" : ""}`}
            />
            {expanded ? "收起" : "展开详情"}
          </button>
        )}

        {expanded && node.output && (
          <div className="mt-2 rounded-md bg-bg p-2 text-xs text-text-muted max-h-48 overflow-y-auto border border-border">
            <pre className="whitespace-pre-wrap break-words font-mono leading-relaxed">
              {node.output}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
