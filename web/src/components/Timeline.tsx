import { useState } from "react";
import { Check, ChevronDown, Loader2 } from "lucide-react";
import type { NodeInfo } from "@/types/events";
import { TimelineNode } from "./TimelineNode";

interface TimelineProps {
  nodes: NodeInfo[];
  isLoading: boolean;
}

export function Timeline({ nodes, isLoading }: TimelineProps) {
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
        <div className="px-3 pb-2 border-t border-border/40">
          {nodes.length === 0 ? (
            <div className="py-4 text-center text-sm text-text-muted">
              等待执行...
            </div>
          ) : (
            <div className="py-2">
              {nodes.map((node, index) => (
                <TimelineNode
                  key={`${node.name}-${index}`}
                  node={node}
                  isLast={index === nodes.length - 1}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
