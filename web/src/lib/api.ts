const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// Chat
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  content: string;
  session_id: string;
  model: string;
}

export function sendMessage(
  message: string,
  sessionId = "web-session",
  userId = "web-user"
) {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId, user_id: userId }),
  });
}

// Memory
export function listMemories(userId: string) {
  return request<{ memories: Record<string, unknown>[] }>(
    `/api/memory/${encodeURIComponent(userId)}`
  );
}

export function deleteMemory(memoryId: string) {
  return request<{ deleted: boolean }>(`/api/memory/${encodeURIComponent(memoryId)}`, {
    method: "DELETE",
  });
}

// Skills
export function listSkills() {
  return request<{ skills: Record<string, unknown>[] }>("/api/skills");
}

export function createSkill(name: string, description: string, code: string) {
  return request<{ saved: boolean; path: string }>("/api/skills", {
    method: "POST",
    body: JSON.stringify({ name, description, code }),
  });
}

// Schedules
export interface Schedule {
  id: string;
  name: string;
  cron: string;
  description: string;
  enabled: boolean;
  payload: Record<string, unknown>;
  timezone: string;
  notification_channel: string | null;
  created_at: string;
  last_run: string | null;
}

export function listSchedules() {
  return request<{ schedules: Schedule[] }>("/api/schedules");
}

export function createSchedule(data: {
  name: string;
  cron: string;
  description?: string;
  payload?: Record<string, unknown>;
  timezone?: string;
  notification_channel?: string;
}) {
  return request<Schedule>("/api/schedules", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateSchedule(id: string, data: Partial<Schedule>) {
  return request<Schedule>(`/api/schedules/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteSchedule(id: string) {
  return request<{ deleted: boolean }>(
    `/api/schedules/${encodeURIComponent(id)}`,
    { method: "DELETE" }
  );
}

// Soul
export function getSoul() {
  return request<{ content: string }>("/api/soul");
}

export function updateSoul(content: string) {
  return request<{ saved: boolean }>("/api/soul", {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
}

// Channels
export interface Channel {
  name: string;
  configured: boolean;
  status: string;
}

export function listChannels() {
  return request<{ channels: Channel[] }>("/api/channels");
}

// Settings
export interface Settings {
  default_model: string;
  reasoning_model: string | null;
  telegram_configured: boolean;
  teams_configured: boolean;
  apprise_default_url_configured: boolean;
  api_host: string;
  api_port: number;
}

export function getSettings() {
  return request<Settings>("/api/settings");
}

export function updateSettings(data: Partial<Settings>) {
  return request<{ updated: boolean }>("/api/settings", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// Notification Channels
export interface NotificationChannel {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
  is_default: boolean;
}

export function listNotificationChannels() {
  return request<{ channels: NotificationChannel[] }>("/api/notifications/channels");
}

export function createNotificationChannel(data: {
  name: string;
  url: string;
  enabled?: boolean;
  is_default?: boolean;
}) {
  return request<NotificationChannel>("/api/notifications/channels", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateNotificationChannel(id: string, data: Partial<NotificationChannel>) {
  return request<NotificationChannel>(
    `/api/notifications/channels/${encodeURIComponent(id)}`,
    {
      method: "PUT",
      body: JSON.stringify(data),
    }
  );
}

export function deleteNotificationChannel(id: string) {
  return request<{ deleted: boolean }>(
    `/api/notifications/channels/${encodeURIComponent(id)}`,
    { method: "DELETE" }
  );
}

export function testNotification(data: {
  message?: string;
  title?: string;
  channel_id?: string;
}) {
  return request<{ sent: boolean; channels: string[] }>("/api/notifications/test", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Skills (user-created SKILL.md format)
export function createUserSkill(data: {
  name: string;
  description: string;
  content: string;
  category?: string;
}) {
  return request<{ saved: boolean; path: string }>("/api/skills", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Health
export function healthCheck() {
  return request<{ status: string; version: string }>("/api/health");
}
