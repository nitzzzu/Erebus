"use client";

import { Loader2, Brain } from "lucide-react";

export function ThinkingIndicator() {
  return (
    <div className="flex items-start gap-3 py-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
        <Brain className="h-4 w-4 text-primary" />
      </div>
      <div className="flex items-center gap-2 rounded-2xl bg-card px-4 py-3">
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        <span className="text-sm text-muted-foreground">
          Thinking
          <span className="inline-flex animate-pulse">
            <span className="mx-px">.</span>
            <span className="mx-px animation-delay-200">.</span>
            <span className="mx-px animation-delay-400">.</span>
          </span>
        </span>
      </div>
    </div>
  );
}
