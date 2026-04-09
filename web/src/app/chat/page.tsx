"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { sendMessage, type ChatMessage } from "@/lib/api";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState<string>("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendMessage(text);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.content },
      ]);
      setModel(res.model);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Failed to send message"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3 sm:px-6">
        <div>
          <h1 className="text-lg font-semibold">Chat</h1>
          <p className="text-xs text-muted-foreground">
            {model ? `Model: ${model}` : "Talk to Erebus"}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setMessages([])}
          disabled={messages.length === 0}
        >
          <RotateCcw className="mr-1 h-3 w-3" />
          New Chat
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4 sm:p-6">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <div className="text-4xl">⚡</div>
              <h2 className="mt-4 text-xl font-semibold">Welcome to Erebus</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Your feature-packed AI agent. Start a conversation below.
              </p>
            </div>
          </div>
        )}

        <div className="mx-auto max-w-3xl space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <Card
                className={`max-w-[85%] px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-card"
                }`}
              >
                <div className="mb-1">
                  <Badge variant={msg.role === "user" ? "secondary" : "outline"} className="text-[10px]">
                    {msg.role === "user" ? "You" : "Erebus"}
                  </Badge>
                </div>
                <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
              </Card>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <Card className="bg-card px-4 py-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Erebus is thinking…
                </div>
              </Card>
            </div>
          )}

          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-4 sm:p-6">
        <div className="mx-auto flex max-w-3xl gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message… (Enter to send, Shift+Enter for new line)"
            className="min-h-[44px] max-h-32 resize-none"
            rows={1}
            disabled={loading}
          />
          <Button onClick={handleSend} disabled={loading || !input.trim()} size="icon" className="shrink-0">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}
