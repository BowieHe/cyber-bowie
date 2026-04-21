import { useState } from "react";
import { Check, ChevronDown, Circle, Loader2 } from "lucide-react";
import type { NodeInfo } from "@/types/events";
import { NODE_NAME_MAP } from "@/types/events";

interface ExecutionFlowProps {
  nodes: NodeInfo[];
  isLoading: boolean;
}

export function ExecutionFlow({ nodes, isLoading }: ExecutionFlowProps) {
  const [expanded, setExpanded] = useState(true);

  const doneCount = nodes.filter((n) => n.status === "done").length;
  const totalCount = nodes.length;

  const title = isLoading
    ? `执行中 (${doneCount}/${totalCount})`
    : totalCount > 0
      ? `执行完成 (${doneCount}/${totalCount})`
      : "执行流程";

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
          {!isLoading && totalCount > 0 && (
            <Check className="h-3 w-3 text-success" />
          )}
          <span className="text-xs font-medium text-text-muted">{title}</span>
        </div>
        <ChevronDown
          className={`h-3.5 w-3.5 text-text-dim transition-transform ${expanded ? "rotate-180" : ""}`}
        />
      </button>

      {expanded && (
        <div className="px-3 pb-2 space-y-1 border-t border-border/40">
          {nodes.map((node) => {
            const displayName = NODE_NAME_MAP[node.name] || node.name;
            const duration =
              node.endTime && node.startTime
                ? ((node.endTime - node.startTime) / 1000).toFixed(1)
                : null;

            return (
              <div key={node.name} className="flex items-center gap-2 py-0.5">
                {node.status === "running" ? (
                  <Loader2 className="h-3 w-3 animate-spin text-accent shrink-0" />
                ) : node.status === "done" ? (
                  <Check className="h-3 w-3 text-success shrink-0" />
                ) : (
                  <Circle className="h-3 w-3 text-text-dim shrink-0" />
                )}
                <span className="text-xs text-text">{displayName}</span>
                {duration && (
                  <span className="text-xs text-text-dim">{duration}s</span>
                )}
                {node.status === "running" && (
                  <span className="text-xs text-accent animate-pulse-dot">
                    运行中
                  </span>
                )}
              </div>
            );
          })}
          {nodes.length === 0 && (
            <div className="py-1 text-xs text-text-dim">等待执行...</div>
          )}
        </div>
      )}
    </div>
  );
}
