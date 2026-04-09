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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const navItems = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/memory", label: "Memory", icon: Brain },
  { href: "/skills", label: "Skills", icon: Zap },
  { href: "/schedules", label: "Schedules", icon: Clock },
  { href: "/soul", label: "Soul", icon: Ghost },
  { href: "/channels", label: "Channels", icon: Radio },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

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
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r bg-card transition-transform duration-200 md:relative md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center border-b px-6">
          <Link href="/chat" className="flex items-center gap-2">
            <span className="text-xl">⚡</span>
            <span className="text-lg font-bold">Erebus</span>
          </Link>
        </div>

        <nav className="flex-1 space-y-1 p-3">
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

        <div className="border-t p-4">
          <div className="text-xs text-muted-foreground">
            Erebus v0.1.0 — Powered by Agno
          </div>
        </div>
      </aside>
    </>
  );
}
