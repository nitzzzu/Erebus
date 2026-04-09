"use client";

import { useState, useEffect, useCallback } from "react";
import { Ghost, Save, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getSoul, updateSoul } from "@/lib/api";

export default function SoulPage() {
  const [content, setContent] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const fetchSoul = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getSoul();
      setContent(data.content);
      setOriginalContent(data.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch soul");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSoul();
  }, [fetchSoul]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await updateSoul(content);
      setOriginalContent(content);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save soul");
    } finally {
      setSaving(false);
    }
  };

  const isDirty = content !== originalContent;

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b px-4 py-3 sm:px-6">
        <div>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Ghost className="h-5 w-5" /> Soul / Personality
          </h1>
          <p className="text-xs text-muted-foreground">
            Define the agent&apos;s personality, tone, and behavior
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setContent(originalContent)}
            disabled={!isDirty}
          >
            <RotateCcw className="mr-1 h-3 w-3" />
            Reset
          </Button>
          <Button size="sm" onClick={handleSave} disabled={saving || !isDirty}>
            {saving ? (
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            ) : (
              <Save className="mr-1 h-3 w-3" />
            )}
            Save
          </Button>
        </div>
      </div>

      <div className="flex-1 p-4 sm:p-6">
        {error && (
          <div className="mb-4 rounded-lg border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {saved && (
          <div className="mb-4 rounded-lg border border-green-500/30 bg-green-500/10 p-3 text-sm text-green-400">
            ✓ Soul saved successfully
          </div>
        )}

        <Card className="h-full">
          <CardHeader>
            <CardTitle className="text-sm">SOUL.md</CardTitle>
            <CardDescription>
              Markdown content that shapes the agent&apos;s personality. Similar to Hermes&apos; SOUL.md.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <Textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="min-h-[400px] font-mono text-sm resize-y"
                placeholder="# Your Agent's Soul&#10;&#10;Define personality, tone, and behavioral constraints in Markdown..."
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
