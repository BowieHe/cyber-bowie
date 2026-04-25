import { useState } from "react";
import {
  Check,
  ChevronDown,
  Loader2,
  Search,
  X,
  Wrench,
  FileText,
  ListOrdered,
  AlertTriangle,
  Lightbulb,
} from "lucide-react";
import type { NodeInfo, ToolCall } from "@/types/events";
import { NODE_NAME_MAP } from "@/types/events";
import { MarkdownRender } from "./MarkdownRender";

interface TimelineNodeProps {
  node: NodeInfo;
  isLast: boolean;
}

function ToolCallCard({ tc }: { tc: ToolCall }) {
  const [expanded, setExpanded] = useState(false);

  const query =
    (tc.args.query as string) ||
    (tc.args.input as string) ||
    (tc.args.question as string) ||
    "";

  const resultPreview = tc.result
    ? tc.result.length > 120
      ? tc.result.slice(0, 120) + "..."
      : tc.result
    : "";

  return (
    <div className="mt-1.5 rounded-md border border-border bg-surface overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-2.5 py-1.5 text-left hover:bg-surface-hover transition-colors"
      >
        <Wrench className="h-3 w-3 text-text-dim" />
        <span className="text-xs font-medium text-text">{tc.name}</span>
        {query && (
          <span className="text-xs text-text-muted truncate flex-1">
            {query}
          </span>
        )}
        <ChevronDown
          className={`h-3 w-3 text-text-dim transition-transform ${expanded ? "rotate-180" : ""}`}
        />
      </button>

      {expanded && (
        <div className="px-3 py-2 text-xs border-t border-border space-y-2">
          {query && (
            <div>
              <span className="text-text-dim">查询：</span>
              <span className="text-text font-mono">{query}</span>
            </div>
          )}
          {Object.keys(tc.args).length > 0 && (
            <div>
              <span className="text-text-dim">参数：</span>
              <pre className="mt-0.5 whitespace-pre-wrap break-words font-mono text-text-muted bg-bg rounded px-2 py-1">
                {JSON.stringify(tc.args, null, 2)}
              </pre>
            </div>
          )}
          {tc.result && (
            <div>
              <span className="text-text-dim">结果：</span>
              <pre className="mt-0.5 whitespace-pre-wrap break-words font-mono text-text-muted bg-bg rounded px-2 py-1 max-h-40 overflow-y-auto">
                {tc.result}
              </pre>
            </div>
          )}
        </div>
      )}

      {!expanded && resultPreview && (
        <div className="px-3 py-1 text-xs text-text-muted border-t border-border truncate">
          {resultPreview}
        </div>
      )}
    </div>
  );
}

function ContentSection({
  title,
  icon,
  children,
  defaultExpanded = false,
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  return (
    <div className="mt-2 rounded-md border border-border bg-bg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-1.5 px-2.5 py-1.5 text-left hover:bg-surface-hover transition-colors"
      >
        {icon}
        <span className="text-xs font-medium text-text">{title}</span>
        <ChevronDown
          className={`h-3 w-3 text-text-dim transition-transform ml-auto ${expanded ? "rotate-180" : ""}`}
        />
      </button>
      {expanded && (
        <div className="px-3 py-2 border-t border-border">{children}</div>
      )}
    </div>
  );
}

function PlanContent({ plan }: { plan: unknown }) {
  const items = Array.isArray(plan)
    ? plan.filter((p): p is string => typeof p === "string")
    : [];
  if (items.length === 0) return null;
  return (
    <ol className="space-y-1">
      {items.map((step, i) => (
        <li key={i} className="text-xs text-text-muted flex gap-2">
          <span className="text-text-dim shrink-0">{i + 1}.</span>
          <span>{step}</span>
        </li>
      ))}
    </ol>
  );
}

function ContextList({ items }: { items: unknown }) {
  const list = Array.isArray(items)
    ? items.filter((i): i is string => typeof i === "string")
    : [];
  if (list.length === 0) return null;
  return (
    <div className="space-y-1.5 max-h-48 overflow-y-auto">
      {list.map((ctx, i) => (
        <div
          key={i}
          className="text-xs text-text-muted bg-surface rounded px-2 py-1.5 border border-border/60"
        >
          <div className="text-text-dim mb-0.5">片段 {i + 1}</div>
          <p className="whitespace-pre-wrap leading-relaxed">{ctx}</p>
        </div>
      ))}
    </div>
  );
}

function SubAgentResults({ results }: { results: unknown }) {
  const list = Array.isArray(results) ? results : [];
  if (list.length === 0) return null;
  return (
    <div className="space-y-2">
      {list.map((r, i) => {
        const topic =
          typeof r === "object" && r !== null ? (r as Record<string, unknown>).topic : "";
        const summary =
          typeof r === "object" && r !== null ? (r as Record<string, unknown>).summary : "";
        return (
          <div
            key={i}
            className="text-xs bg-surface rounded px-2.5 py-2 border border-border/60"
          >
            <div className="font-medium text-text mb-1">
              {typeof topic === "string" ? topic : `子代理 ${i + 1}`}
            </div>
            {typeof summary === "string" && (
              <p className="text-text-muted whitespace-pre-wrap leading-relaxed">{summary}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}

function VerificationResults({ results }: { results: unknown }) {
  if (!results) return null;
  if (Array.isArray(results)) {
    return (
      <div className="space-y-1.5">
        {results.map((r, i) => (
          <pre
            key={i}
            className="text-xs text-text-muted whitespace-pre-wrap break-words bg-surface rounded px-2 py-1.5 border border-border/60"
          >
            {JSON.stringify(r, null, 2)}
          </pre>
        ))}
      </div>
    );
  }
  return (
    <pre className="text-xs text-text-muted whitespace-pre-wrap break-words bg-surface rounded px-2 py-1.5 border border-border/60">
      {JSON.stringify(results, null, 2)}
    </pre>
  );
}

function MarkdownSection({ content }: { content: string }) {
  if (!content) return null;
  return (
    <div className="text-xs max-h-64 overflow-y-auto">
      <MarkdownRender content={content} />
    </div>
  );
}

function NodeStructuredContent({ node }: { node: NodeInfo }) {
  const data = node.data;
  if (!data) return null;

  const sections: React.ReactNode[] = [];

  // Plan node: show execution plan
  if (node.name === "plan_node" && data.plan) {
    sections.push(
      <ContentSection key="plan" title="执行计划" icon={<ListOrdered className="h-3 w-3 text-accent" />}>
        <PlanContent plan={data.plan} />
      </ContentSection>
    );
  }

  // Research plan (from research supervisor internal plan node)
  if (data.research_plan && Array.isArray(data.research_plan) && data.research_plan.length > 0) {
    sections.push(
      <ContentSection key="research_plan" title="研究计划" icon={<Lightbulb className="h-3 w-3 text-accent" />}>
        <PlanContent plan={data.research_plan} />
      </ContentSection>
    );
  }

  // Router: show routing decision
  if (node.name === "router" && data.next_agent) {
    const next = String(data.next_agent);
    const nextName = NODE_NAME_MAP[next] || next;
    sections.push(
      <div key="route" className="mt-1.5 text-xs text-text-muted">
        <span className="text-text-dim">下一步：</span>
        <span className="text-accent font-medium">{nextName}</span>
      </div>
    );
  }

  // Retrieved context (research results)
  if (data.retrieved_context) {
    sections.push(
      <ContentSection key="context" title="检索结果" icon={<Search className="h-3 w-3 text-accent" />}>
        <ContextList items={data.retrieved_context} />
      </ContentSection>
    );
  }

  // Sub-agent results
  if (data.sub_agent_results) {
    sections.push(
      <ContentSection key="subagents" title="子代理结果" icon={<FileText className="h-3 w-3 text-accent" />}>
        <SubAgentResults results={data.sub_agent_results} />
      </ContentSection>
    );
  }

  // Draft
  if (data.draft && typeof data.draft === "string") {
    sections.push(
      <ContentSection key="draft" title="草稿" icon={<FileText className="h-3 w-3 text-accent" />}>
        <MarkdownSection content={data.draft} />
      </ContentSection>
    );
  }

  // Final answer / output (from synthesizer or chat_agent)
  if (data.final_answer && typeof data.final_answer === "string") {
    sections.push(
      <ContentSection key="final" title="最终答案" icon={<FileText className="h-3 w-3 text-accent" />} defaultExpanded>
        <MarkdownSection content={data.final_answer} />
      </ContentSection>
    );
  } else if (
    (node.name === "chat_agent" || node.name === "chat_llm") &&
    data.output &&
    typeof data.output === "string"
  ) {
    sections.push(
      <ContentSection key="output" title="回复" icon={<FileText className="h-3 w-3 text-accent" />}>
        <MarkdownSection content={data.output} />
      </ContentSection>
    );
  }

  // Verification results
  if (data.verification_results) {
    sections.push(
      <ContentSection key="verify" title="质检结果" icon={<AlertTriangle className="h-3 w-3 text-warning" />}>
        <VerificationResults results={data.verification_results} />
      </ContentSection>
    );
  }

  // Missing information / harness status (from reflect)
  if (data.missing_information && typeof data.missing_information === "string") {
    sections.push(
      <div key="missing" className="mt-1.5 rounded-md bg-warning/10 border border-warning/30 px-2.5 py-1.5">
        <div className="text-xs font-medium text-warning mb-0.5">缺失信息</div>
        <p className="text-xs text-text-muted whitespace-pre-wrap">{data.missing_information}</p>
      </div>
    );
  }

  if (data.current_harness_status && typeof data.current_harness_status === "string") {
    const status = String(data.current_harness_status);
    const isPass = status === "PASS" || status === "ACCEPT";
    sections.push(
      <div
        key="harness"
        className={`mt-1.5 rounded-md px-2.5 py-1.5 border ${
          isPass
            ? "bg-success/10 border-success/30"
            : "bg-warning/10 border-warning/30"
        }`}
      >
        <div className={`text-xs font-medium ${isPass ? "text-success" : "text-warning"}`}>
          评估状态：{status}
        </div>
      </div>
    );
  }

  // Execution log
  if (data.execution_log && Array.isArray(data.execution_log) && data.execution_log.length > 0) {
    const logs = data.execution_log.filter((l): l is string => typeof l === "string");
    if (logs.length > 0) {
      sections.push(
        <ContentSection key="logs" title="执行日志">
          <div className="space-y-0.5">
            {logs.map((log, i) => (
              <div key={i} className="text-xs text-text-muted font-mono">
                {log}
              </div>
            ))}
          </div>
        </ContentSection>
      );
    }
  }

  if (sections.length === 0) return null;
  return <div className="mt-1">{sections}</div>;
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

  const hasToolCalls = (node.toolCalls?.length ?? 0) > 0;
  const hasStructuredContent = !!node.data;
  const hasExpandableContent =
    hasStructuredContent || (node.output?.length ?? 0) > 100;

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
          {hasToolCalls && (
            <span className="flex items-center gap-0.5 text-xs text-text-muted">
              <Search className="h-3 w-3" />
              {node.toolCalls!.length}
            </span>
          )}
        </div>

        {node.statusMessage && (
          <p className="mt-0.5 text-xs text-text-muted line-clamp-1">
            {node.statusMessage}
          </p>
        )}

        {/* Tool calls */}
        {hasToolCalls && (
          <div className="mt-1.5 space-y-1">
            {node.toolCalls!.map((tc, i) => (
              <ToolCallCard key={`${tc.name}-${i}`} tc={tc} />
            ))}
          </div>
        )}

        {/* Structured content from node data */}
        {hasStructuredContent && <NodeStructuredContent node={node} />}

        {/* Fallback expandable raw output */}
        {hasExpandableContent && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-1 flex items-center gap-0.5 text-xs text-text-dim hover:text-text transition-colors"
          >
            <ChevronDown
              className={`h-3 w-3 transition-transform ${expanded ? "rotate-180" : ""}`}
            />
            {expanded ? "收起原始数据" : "展开原始数据"}
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
