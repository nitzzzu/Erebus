"use client";

import { Wrench, CheckCircle2, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { ToolCallEvent } from "@/lib/api-client";

export function ToolCallCard({ tool }: { tool: ToolCallEvent }) {
  const [expanded, setExpanded] = useState(false);
  const isRunning = tool.status === "running";

  return (
    <div className="my-2 rounded-lg border border-border bg-card/50">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-accent/50 transition-colors rounded-lg"
      >
        {isRunning ? (
          <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-primary" />
        ) : (
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-green-500" />
        )}
        <Wrench className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        <span className="font-mono text-xs font-medium text-foreground">
          {tool.name}
        </span>
        {isRunning && (
          <span className="ml-1 text-xs text-muted-foreground">Running…</span>
        )}
        <span className="ml-auto">
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
          )}
        </span>
      </button>

      {expanded && (
        <div className="border-t border-border px-3 py-2 space-y-2">
          {tool.args && (
            <div>
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                Arguments
              </span>
              <pre className="mt-1 max-h-32 overflow-auto rounded bg-muted/50 p-2 text-xs font-mono text-muted-foreground">
                {tool.args}
              </pre>
            </div>
          )}
          {tool.result && (
            <div>
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                Result
              </span>
              <pre className="mt-1 max-h-48 overflow-auto rounded bg-muted/50 p-2 text-xs font-mono text-muted-foreground">
                {tool.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ToolCallList({ tools }: { tools: ToolCallEvent[] }) {
  if (tools.length === 0) return null;

  return (
    <div className="space-y-1">
      {tools.map((tool, i) => (
        <ToolCallCard key={`${tool.name}-${i}`} tool={tool} />
      ))}
    </div>
  );
}
