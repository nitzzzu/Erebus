"use client";

import { useState, useEffect, useCallback } from "react";
import { Clock, Plus, Trash2, Loader2, X, Play, Pause } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { listSchedules, createSchedule, updateSchedule, deleteSchedule, type Schedule } from "@/lib/api";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", cron: "", description: "", timezone: "UTC", notification_channel: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedules = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listSchedules();
      setSchedules(data.schedules);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch schedules");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSchedules();
  }, [fetchSchedules]);

  const handleCreate = async () => {
    if (!form.name || !form.cron) return;
    setSaving(true);
    setError(null);
    try {
      await createSchedule({
        ...form,
        notification_channel: form.notification_channel || undefined,
      });
      setForm({ name: "", cron: "", description: "", timezone: "UTC", notification_channel: "" });
      setShowCreate(false);
      await fetchSchedules();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create schedule");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      await updateSchedule(id, { enabled });
      setSchedules((prev) =>
        prev.map((s) => (s.id === id ? { ...s, enabled } : s))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update schedule");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteSchedule(id);
      setSchedules((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete schedule");
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b px-4 py-3 sm:px-6">
        <div>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Clock className="h-5 w-5" /> Schedules
          </h1>
          <p className="text-xs text-muted-foreground">
            Manage cron-based scheduled tasks
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? <X className="mr-1 h-3 w-3" /> : <Plus className="mr-1 h-3 w-3" />}
          {showCreate ? "Cancel" : "New Schedule"}
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
              <CardTitle className="text-sm">Create Schedule</CardTitle>
              <CardDescription>Set up a new cron-based automated task</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="sched-name">Name</Label>
                  <Input
                    id="sched-name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="e.g., daily-report"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sched-cron">Cron Expression</Label>
                  <Input
                    id="sched-cron"
                    value={form.cron}
                    onChange={(e) => setForm({ ...form, cron: e.target.value })}
                    placeholder="0 9 * * *"
                    className="font-mono"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="sched-desc">Description</Label>
                <Input
                  id="sched-desc"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="What does this schedule do?"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sched-tz">Timezone</Label>
                <Input
                  id="sched-tz"
                  value={form.timezone}
                  onChange={(e) => setForm({ ...form, timezone: e.target.value })}
                  placeholder="UTC"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sched-notify">Notification Channel (optional)</Label>
                <Input
                  id="sched-notify"
                  value={form.notification_channel}
                  onChange={(e) => setForm({ ...form, notification_channel: e.target.value })}
                  placeholder="channel name (leave blank for default)"
                />
              </div>
              <Button onClick={handleCreate} disabled={saving || !form.name || !form.cron}>
                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                Create Schedule
              </Button>
            </CardContent>
          </Card>
        )}

        <ScrollArea className="h-[calc(100vh-220px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : schedules.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="mx-auto h-12 w-12 text-muted-foreground/30" />
              <p className="mt-4 text-sm text-muted-foreground">No schedules configured</p>
            </div>
          ) : (
            <div className="space-y-3">
              {schedules.map((schedule) => (
                <Card key={schedule.id}>
                  <CardContent className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm truncate">{schedule.name}</span>
                        <Badge variant={schedule.enabled ? "default" : "secondary"} className="text-[10px]">
                          {schedule.enabled ? "Active" : "Paused"}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground space-y-0.5">
                        <div className="font-mono">{schedule.cron}</div>
                        {schedule.description && <div>{schedule.description}</div>}
                        <div>Timezone: {schedule.timezone}</div>
                        {schedule.notification_channel && (
                          <div>Notify: {schedule.notification_channel}</div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="flex items-center gap-2">
                        {schedule.enabled ? (
                          <Pause className="h-3 w-3 text-muted-foreground" />
                        ) : (
                          <Play className="h-3 w-3 text-muted-foreground" />
                        )}
                        <Switch
                          checked={schedule.enabled}
                          onCheckedChange={(checked) => handleToggle(schedule.id, checked)}
                        />
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={() => handleDelete(schedule.id)}
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
