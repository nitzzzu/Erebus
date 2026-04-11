"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, User, Bot, FolderOpen, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { MarkdownContent } from "@/components/markdown-content";
import { ToolCallCard, ToolCallList } from "@/components/tool-call-card";
import { ThinkingIndicator } from "@/components/thinking-indicator";
import { WorkspaceFileExplorer } from "@/components/workspace-file-explorer";
import { useChat } from "@/store/chat-context";
import { listWorkspaces, type ContentBlock } from "@/lib/api-client";

interface Workspace {
  name: string;
  path: string;
  description: string;
}

export default function ChatPage() {
  const { state, sendChat, newSession } = useChat();
  const { messages, busy, model, streamBlocks } = state;
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Workspace file explorer panel
  const [explorerOpen, setExplorerOpen] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<string | null>(null);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);

  useEffect(() => {
    listWorkspaces()
      .then((d) => setWorkspaces(d.workspaces as Workspace[]))
      .catch((err) => {
        // Workspace loading is optional — show a non-blocking warning
        setWorkspaceError(err instanceof Error ? err.message : "Failed to load workspaces");
      });
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamBlocks]);

  // Auto-focus textarea
  useEffect(() => {
    textareaRef.current?.focus();
  }, [messages]);

  const handleSend = useCallback(() => {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    sendChat(text);
  }, [input, busy, sendChat]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Ctrl+N for new chat
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "n") {
        e.preventDefault();
        newSession();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [newSession]);

  const handleWorkspaceSelect = (name: string) => {
    setActiveWorkspace(name);
    setExplorerOpen(true);
  };

  const handleExplorerClose = () => {
    setExplorerOpen(false);
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main chat column */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Workspace loading error (non-blocking notice) */}
        {workspaceError && (
          <div className="flex items-center justify-between px-4 py-1.5 bg-destructive/10 text-destructive text-xs border-b border-destructive/20">
            <span>Workspaces unavailable: {workspaceError}</span>
            <button
              className="ml-2 opacity-70 hover:opacity-100"
              onClick={() => setWorkspaceError(null)}
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        )}
        {/* Workspace / explorer toolbar — only shown when a workspace is selected */}
        {(workspaces.length > 0 || activeWorkspace) && (
          <div className="flex items-center gap-2 border-b px-4 py-2 shrink-0">
            {workspaces.length > 0 && (
              activeWorkspace && explorerOpen ? (
                <Button variant="outline" size="sm" onClick={handleExplorerClose}>
                  <X className="mr-1.5 h-3.5 w-3.5" />
                  {activeWorkspace}
                </Button>
              ) : (
                <select
                  className="h-8 rounded-md border border-input bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                  value={activeWorkspace ?? ""}
                  onChange={(e) => { const v = e.target.value; if (v) handleWorkspaceSelect(v); }}
                >
                  <option value="">Workspace…</option>
                  {workspaces.map((ws) => (
                    <option key={ws.name} value={ws.name}>{ws.name}</option>
                  ))}
                </select>
              )
            )}
            {activeWorkspace && !explorerOpen && (
              <Button variant="outline" size="sm" onClick={() => setExplorerOpen(true)} title="Open file explorer">
                <FolderOpen className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        )}

        {/* Messages */}
        <ScrollArea className="flex-1 p-4 sm:p-6">
          {messages.length === 0 && !busy && (
            <div className="flex h-full min-h-[60vh] items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                  <Bot className="h-8 w-8 text-primary" />
                </div>
                <h2 className="text-xl font-semibold">Welcome to Erebus</h2>
                <p className="mt-2 max-w-md text-sm text-muted-foreground">
                  Your autonomous AI agent with memory, skills, and tool use.
                  Start a conversation below.
                </p>
                <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
                  {[
                    "What can you help me with?",
                    "Search the web for latest AI news",
                    "Read and summarize a file",
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => {
                        setInput(suggestion);
                        textareaRef.current?.focus();
                      }}
                      className="rounded-full border border-border px-4 py-2 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="mx-auto max-w-3xl space-y-1">
            {messages.map((msg, i) => (
              <div key={i} className="group">
                {msg.role === "user" ? (
                  <div className="flex items-start gap-3 py-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
                      <User className="h-4 w-4 text-primary-foreground" />
                    </div>
                    <div className="min-w-0 flex-1 pt-1">
                      <div className="mb-1 text-xs font-medium text-muted-foreground">You</div>
                      <div className="whitespace-pre-wrap text-sm leading-relaxed">
                        {msg.content}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-3 py-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-card border border-border">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1 pt-1">
                      <div className="mb-1 flex items-center gap-2">
                        <span className="text-xs font-medium text-muted-foreground">Erebus</span>
                        {model && (
                          <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                            {model}
                          </Badge>
                        )}
                      </div>
                      {/* Render inline content blocks in order (tool calls interleaved with text) */}
                      {msg.content_blocks && msg.content_blocks.length > 0 ? (
                        <div className="text-sm leading-relaxed space-y-1">
                          {msg.content_blocks.map((block, blockIndex) =>
                            block.type === "tool" ? (
                              <ToolCallCard key={blockIndex} tool={block.tool} />
                            ) : (
                              block.text && (
                                <MarkdownContent key={blockIndex} content={block.text} />
                              )
                            )
                          )}
                        </div>
                      ) : (
                        <>
                          {msg.tool_calls && msg.tool_calls.length > 0 && (
                            <ToolCallList tools={msg.tool_calls} />
                          )}
                          <div className="text-sm leading-relaxed">
                            <MarkdownContent content={msg.content} />
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Active streaming content — inline blocks in arrival order */}
            {busy && (
              <div className="flex items-start gap-3 py-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-card border border-border">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <div className="min-w-0 flex-1 pt-1">
                  {streamBlocks.length > 0 ? (
                    <div className="text-sm leading-relaxed space-y-1">
                      {streamBlocks.map((block, blockIndex) =>
                        block.type === "tool" ? (
                          <ToolCallCard key={blockIndex} tool={block.tool} />
                        ) : (
                          block.text && (
                            <div key={blockIndex}>
                              <MarkdownContent content={block.text} />
                              {/* Show cursor only after last text block */}
                              {blockIndex === streamBlocks.length - 1 && (
                                <span className="inline-block h-4 w-0.5 animate-pulse bg-primary ml-0.5" />
                              )}
                            </div>
                          )
                        )
                      )}
                    </div>
                  ) : (
                    <ThinkingIndicator />
                  )}
                </div>
              </div>
            )}

            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        {/* Composer */}
        <div className="border-t bg-background p-4 sm:p-6 shrink-0">
          <div className="mx-auto flex max-w-3xl gap-2">
            <div className="relative flex-1">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  busy
                    ? "Waiting for response…"
                    : "Message Erebus… (Enter to send, Shift+Enter for newline)"
                }
                className="min-h-[52px] max-h-40 resize-none pr-4"
                rows={1}
                disabled={busy}
              />
            </div>
            <Button
              onClick={handleSend}
              disabled={busy || !input.trim()}
              size="icon"
              className="h-[52px] w-[52px] shrink-0 rounded-xl"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <div className="mx-auto mt-2 max-w-3xl">
            <p className="text-center text-[10px] text-muted-foreground">
              Erebus has tools, memory, and skills. Type{" "}
              <kbd className="rounded border border-border px-1 py-0.5 font-mono text-[10px]">
                /help
              </kbd>{" "}
              for commands.
            </p>
          </div>
        </div>
      </div>

      {/* Workspace file explorer panel */}
      {explorerOpen && activeWorkspace && (
        <div className="w-64 sm:w-72 shrink-0 border-l border-border overflow-hidden flex flex-col">
          <WorkspaceFileExplorer
            workspaceName={activeWorkspace}
            onClose={handleExplorerClose}
          />
        </div>
      )}
    </div>
  );
}
