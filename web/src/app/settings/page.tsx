"use client";

import { useState, useEffect, useCallback } from "react";
import { Settings as SettingsIcon, Save, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getSettings, updateSettings, type Settings } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [form, setForm] = useState({ default_model: "", reasoning_model: "" });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getSettings();
      setSettings(data);
      setForm({
        default_model: data.default_model,
        reasoning_model: data.reasoning_model || "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await updateSettings({
        default_model: form.default_model || undefined,
        reasoning_model: form.reasoning_model || undefined,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-4 py-3 sm:px-6">
        <h1 className="text-lg font-semibold flex items-center gap-2">
          <SettingsIcon className="h-5 w-5" /> Settings
        </h1>
        <p className="text-xs text-muted-foreground">
          Configure models, channels, and agent behavior
        </p>
      </div>

      <div className="flex-1 p-4 sm:p-6 space-y-6 max-w-2xl">
        {error && (
          <div className="rounded-lg border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {saved && (
          <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-3 text-sm text-green-400">
            ✓ Settings saved successfully
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            {/* Model Configuration */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Model Configuration</CardTitle>
                <CardDescription>
                  Use &quot;provider:model_id&quot; format — e.g., openai:gpt-4o, anthropic:claude-sonnet-4-20250514, openrouter:meta-llama/llama-3-70b
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="default-model">Default Model</Label>
                  <Input
                    id="default-model"
                    value={form.default_model}
                    onChange={(e) => setForm({ ...form, default_model: e.target.value })}
                    placeholder="openai:gpt-4o"
                    className="font-mono text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reasoning-model">Reasoning Model (optional)</Label>
                  <Input
                    id="reasoning-model"
                    value={form.reasoning_model}
                    onChange={(e) => setForm({ ...form, reasoning_model: e.target.value })}
                    placeholder="anthropic:claude-sonnet-4-20250514"
                    className="font-mono text-sm"
                  />
                </div>
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  Save Models
                </Button>
              </CardContent>
            </Card>

            <Separator />

            {/* Channel Status */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Channel Status</CardTitle>
                <CardDescription>
                  Configure channels via environment variables
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Telegram</span>
                  <Badge variant={settings?.telegram_configured ? "default" : "secondary"}>
                    {settings?.telegram_configured ? "Configured" : "Not Set"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Microsoft Teams</span>
                  <Badge variant={settings?.teams_configured ? "default" : "secondary"}>
                    {settings?.teams_configured ? "Configured" : "Not Set"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Apprise (default URL)</span>
                  <Badge variant={settings?.apprise_default_url_configured ? "default" : "secondary"}>
                    {settings?.apprise_default_url_configured ? "Configured" : "Not Set"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Web UI</span>
                  <Badge variant="default">Always Active</Badge>
                </div>
              </CardContent>
            </Card>

            <Separator />

            {/* Server Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Server Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <div className="flex justify-between">
                  <span>API Host</span>
                  <span className="font-mono">{settings?.api_host ?? "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span>API Port</span>
                  <span className="font-mono">{settings?.api_port ?? "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Version</span>
                  <span className="font-mono">0.1.0</span>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
