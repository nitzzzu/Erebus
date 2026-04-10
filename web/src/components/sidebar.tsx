"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  Brain,
  Zap,
  Clock,
  Ghost,
  Radio,
  Settings,
  Menu,
  X,
  Plus,
  Trash2,
  Pencil,
  Check,
  Bell,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useState, useCallback } from "react";
import { useChat } from "@/store/chat-context";

const navItems = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/memory", label: "Memory", icon: Brain },
  { href: "/skills", label: "Skills", icon: Zap },
  { href: "/schedules", label: "Schedules", icon: Clock },
  { href: "/soul", label: "Soul", icon: Ghost },
  { href: "/channels", label: "Channels", icon: Radio },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
];

function SessionItem({
  session,
  isActive,
  onSelect,
  onDelete,
  onRename,
}: {
  session: { session_id: string; title: string; message_count: number };
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: (title: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(session.title);

  const handleRename = useCallback(() => {
    const trimmed = editTitle.trim();
    if (trimmed && trimmed !== session.title) {
      onRename(trimmed);
    }
    setEditing(false);
  }, [editTitle, session.title, onRename]);

  if (editing) {
    return (
      <div className="flex items-center gap-1 rounded-lg bg-accent px-2 py-1.5">
        <input
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleRename();
            if (e.key === "Escape") setEditing(false);
          }}
          onBlur={handleRename}
          className="flex-1 bg-transparent text-xs outline-none"
          autoFocus
        />
        <button onClick={handleRename} className="p-0.5 text-muted-foreground hover:text-foreground">
          <Check className="h-3 w-3" />
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={onSelect}
      className={cn(
        "group flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs transition-colors hover:bg-accent",
        isActive && "bg-accent text-accent-foreground"
      )}
    >
      <MessageSquare className="h-3 w-3 shrink-0 text-muted-foreground" />
      <span className="flex-1 truncate">{session.title}</span>
      <span className="hidden shrink-0 items-center gap-0.5 group-hover:flex">
        <span
          onClick={(e) => {
            e.stopPropagation();
            setEditTitle(session.title);
            setEditing(true);
          }}
          className="rounded p-0.5 hover:bg-background"
        >
          <Pencil className="h-2.5 w-2.5 text-muted-foreground" />
        </span>
        <span
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="rounded p-0.5 hover:bg-background"
        >
          <Trash2 className="h-2.5 w-2.5 text-destructive" />
        </span>
      </span>
    </button>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { state, switchSession, newSession, deleteSession, renameSessionAction } = useChat();

  return (
    <>
      {/* Mobile hamburger */}
      <div className="fixed top-0 left-0 z-50 flex h-14 w-full items-center border-b bg-background px-4 md:hidden">
        <Button variant="ghost" size="icon" onClick={() => setOpen(!open)}>
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
        <span className="ml-3 text-lg font-bold">⚡ Erebus</span>
      </div>

      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r bg-card transition-transform duration-200 md:relative md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo */}
        <div className="flex h-14 items-center justify-between border-b px-4">
          <Link href="/chat" className="flex items-center gap-2">
            <span className="text-xl">⚡</span>
            <span className="text-lg font-bold">Erebus</span>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => {
              newSession();
              setOpen(false);
            }}
            title="New Chat (Ctrl+N)"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="space-y-0.5 px-3 pt-3">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                pathname === href || pathname?.startsWith(href + "/")
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>

        {/* Session list */}
        {state.sessions.length > 0 && (
          <div className="mt-4 flex flex-col overflow-hidden border-t px-3 pt-3">
            <div className="mb-2 flex items-center justify-between px-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Recent Sessions
              </span>
              <span className="text-[10px] text-muted-foreground">
                {state.sessions.length}
              </span>
            </div>
            <ScrollArea className="flex-1">
              <div className="space-y-0.5 pb-4">
                {state.sessions.map((session) => (
                  <SessionItem
                    key={session.session_id}
                    session={session}
                    isActive={session.session_id === state.currentSessionId}
                    onSelect={() => {
                      switchSession(session.session_id);
                      setOpen(false);
                    }}
                    onDelete={() => deleteSession(session.session_id)}
                    onRename={(title) =>
                      renameSessionAction(session.session_id, title)
                    }
                  />
                ))}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Footer */}
        <div className="mt-auto border-t p-4">
          <div className="text-xs text-muted-foreground">
            Erebus v0.1.0 — Powered by Agno
          </div>
        </div>
      </aside>
    </>
  );
}
