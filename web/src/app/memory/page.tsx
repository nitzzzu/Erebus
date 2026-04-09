"use client";

import { useState, useEffect, useCallback } from "react";
import { Brain, Search, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { listMemories, deleteMemory } from "@/lib/api";

export default function MemoryPage() {
  const [userId, setUserId] = useState("web-user");
  const [searchUserId, setSearchUserId] = useState("web-user");
  const [memories, setMemories] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMemories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listMemories(searchUserId);
      setMemories(data.memories);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch memories");
    } finally {
      setLoading(false);
    }
  }, [searchUserId]);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  const handleDelete = async (id: string) => {
    try {
      await deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete memory");
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-4 py-3 sm:px-6">
        <h1 className="text-lg font-semibold flex items-center gap-2">
          <Brain className="h-5 w-5" /> Memory
        </h1>
        <p className="text-xs text-muted-foreground">
          View and manage agent memories across users
        </p>
      </div>

      <div className="p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row gap-2 mb-6">
          <Input
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="User ID"
            className="sm:max-w-xs"
          />
          <Button
            onClick={() => {
              setSearchUserId(userId);
            }}
          >
            <Search className="mr-2 h-4 w-4" />
            Search
          </Button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <ScrollArea className="h-[calc(100vh-220px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : memories.length === 0 ? (
            <div className="text-center py-12">
              <Brain className="mx-auto h-12 w-12 text-muted-foreground/30" />
              <p className="mt-4 text-sm text-muted-foreground">
                No memories found for &quot;{searchUserId}&quot;
              </p>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {memories.map((memory, i) => (
                <Card key={String(memory.id ?? i)}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-sm">
                        Memory #{String(memory.id ?? i).slice(0, 8)}
                      </CardTitle>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 text-muted-foreground hover:text-destructive"
                        onClick={() => handleDelete(String(memory.id))}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                    {Array.isArray(memory.topics) && (memory.topics as unknown[]).length > 0 && (
                      <CardDescription>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {(memory.topics as unknown[]).map(
                            (t: unknown, j: number) => (
                              <Badge key={j} variant="secondary" className="text-[10px]">
                                {String(t)}
                              </Badge>
                            )
                          )}
                        </div>
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      {String(memory.content ?? "")}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
}
