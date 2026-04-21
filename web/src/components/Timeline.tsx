import type { NodeInfo } from "@/types/events";
import { TimelineNode } from "./TimelineNode";

interface TimelineProps {
  nodes: NodeInfo[];
}

export function Timeline({ nodes }: TimelineProps) {
  if (nodes.length === 0) {
    return (
      <div className="py-4 text-center text-sm text-text-muted">
        等待执行...
      </div>
    );
  }

  return (
    <div className="py-2">
      {nodes.map((node, index) => (
        <TimelineNode
          key={`${node.name}-${index}`}
          node={node}
          isLast={index === nodes.length - 1}
        />
      ))}
    </div>
  );
}
