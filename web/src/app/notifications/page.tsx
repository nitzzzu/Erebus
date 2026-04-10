"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Bell,
  Plus,
  Trash2,
  Loader2,
  X,
  Star,
  Send,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  listNotificationChannels,
  createNotificationChannel,
  updateNotificationChannel,
  deleteNotificationChannel,
  testNotification,
  type NotificationChannel,
} from "@/lib/api";

export default function NotificationsPage() {
  const [channels, setChannels] = useState<NotificationChannel[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", url: "", is_default: false });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [testSuccess, setTestSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchChannels = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listNotificationChannels();
      setChannels(data.channels);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch channels");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChannels();
  }, [fetchChannels]);

  const handleCreate = async () => {
    if (!form.name || !form.url) return;
    setSaving(true);
    setError(null);
    try {
      await createNotificationChannel(form);
      setForm({ name: "", url: "", is_default: false });
      setShowCreate(false);
      await fetchChannels();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create channel");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      await updateNotificationChannel(id, { enabled });
      setChannels((prev) => prev.map((c) => (c.id === id ? { ...c, enabled } : c)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update channel");
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await updateNotificationChannel(id, { is_default: true });
      setChannels((prev) =>
        prev.map((c) => ({ ...c, is_default: c.id === id }))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to set default");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteNotificationChannel(id);
      setChannels((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete channel");
    }
  };

  const handleTest = async (id: string) => {
    setTesting(id);
    setTestSuccess(null);
    setError(null);
    try {
      await testNotification({ channel_id: id });
      setTestSuccess(id);
      setTimeout(() => setTestSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Test notification failed");
    } finally {
      setTesting(null);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b px-4 py-3 sm:px-6">
        <div>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Bell className="h-5 w-5" /> Notifications
          </h1>
          <p className="text-xs text-muted-foreground">
            Configure apprise notification channels for agent alerts and briefings
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? <X className="mr-1 h-3 w-3" /> : <Plus className="mr-1 h-3 w-3" />}
          {showCreate ? "Cancel" : "Add Channel"}
        </Button>
      </div>

      <div className="p-4 sm:p-6">
        {error && (
          <div className="mb-4 rounded-lg border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {showCreate && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-sm">Add Notification Channel</CardTitle>
              <CardDescription>
                Enter an{" "}
                <a
                  href="https://github.com/caronc/apprise/wiki"
                  target="_blank"
                  rel="noreferrer"
                  className="underline"
                >
                  apprise
                </a>{" "}
                URL (e.g.{" "}
                <code className="text-xs font-mono">tgram://bottoken/chatid</code>,{" "}
                <code className="text-xs font-mono">mailto://user:pass@gmail.com</code>)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="ch-name">Name</Label>
                  <Input
                    id="ch-name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="e.g., telegram, my-email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ch-url">Apprise URL</Label>
                  <Input
                    id="ch-url"
                    value={form.url}
                    onChange={(e) => setForm({ ...form, url: e.target.value })}
                    placeholder="tgram://bottoken/chatid"
                    className="font-mono text-sm"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  id="ch-default"
                  checked={form.is_default}
                  onCheckedChange={(checked) => setForm({ ...form, is_default: checked })}
                />
                <Label htmlFor="ch-default">Set as default channel</Label>
              </div>
              <Button onClick={handleCreate} disabled={saving || !form.name || !form.url}>
                {saving ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="mr-2 h-4 w-4" />
                )}
                Add Channel
              </Button>
            </CardContent>
          </Card>
        )}

        <ScrollArea className="h-[calc(100vh-220px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : channels.length === 0 ? (
            <div className="text-center py-12">
              <Bell className="mx-auto h-12 w-12 text-muted-foreground/30" />
              <p className="mt-4 text-sm text-muted-foreground">No notification channels configured</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Add an apprise URL to enable agent notifications
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {channels.map((ch) => (
                <Card key={ch.id}>
                  <CardContent className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm">{ch.name}</span>
                        {ch.is_default && (
                          <Badge variant="default" className="text-[10px]">
                            Default
                          </Badge>
                        )}
                        <Badge
                          variant={ch.enabled ? "default" : "secondary"}
                          className="text-[10px]"
                        >
                          {ch.enabled ? "Enabled" : "Disabled"}
                        </Badge>
                        {testSuccess === ch.id && (
                          <span className="flex items-center gap-1 text-xs text-green-500">
                            <CheckCircle2 className="h-3 w-3" /> Sent
                          </span>
                        )}
                      </div>
                      <div className="font-mono text-xs text-muted-foreground truncate max-w-sm">
                        {ch.url}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Switch
                        checked={ch.enabled}
                        onCheckedChange={(checked) => handleToggle(ch.id, checked)}
                      />
                      {!ch.is_default && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground"
                          title="Set as default"
                          onClick={() => handleSetDefault(ch.id)}
                        >
                          <Star className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground"
                        title="Send test notification"
                        onClick={() => handleTest(ch.id)}
                        disabled={testing === ch.id || !ch.enabled}
                      >
                        {testing === ch.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={() => handleDelete(ch.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
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
