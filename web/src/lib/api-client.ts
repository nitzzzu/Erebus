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

// ── Types ─────────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  tool_calls?: ToolCallEvent[];
}

export interface ChatResponse {
  content: string;
  session_id: string;
  model: string;
}

export interface ToolCallEvent {
  name: string;
  args?: string;
  result?: string;
  status: "running" | "completed" | "error";
}

export interface SessionCompact {
  session_id: string;
  title: string;
  model: string;
  message_count: number;
  created_at: number;
  updated_at: number;
  pinned: boolean;
  archived: boolean;
}

export interface SessionFull {
  session_id: string;
  title: string;
  model: string;
  messages: { role: string; content: string }[];
  created_at: number;
  updated_at: number;
  pinned: boolean;
  archived: boolean;
  tool_calls: Record<string, unknown>[];
}

export interface Channel {
  name: string;
  configured: boolean;
  status: string;
}

export interface Schedule {
  id: string;
  name: string;
  cron: string;
  description: string;
  enabled: boolean;
  payload: Record<string, unknown>;
  timezone: string;
  created_at: string;
  last_run: string | null;
}

export interface Settings {
  default_model: string;
  reasoning_model: string | null;
  skills_dir: string | null;
  telegram_configured: boolean;
  teams_configured: boolean;
  api_host: string;
  api_port: number;
}

// ── Chat (sync, backward compat) ──────────────────────────────────────────

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

// ── Chat (SSE Streaming) ──────────────────────────────────────────────────

export interface StreamStartResponse {
  stream_id: string;
  session_id: string;
}

export function startChatStream(
  message: string,
  sessionId?: string,
  userId = "web-user",
  model?: string
) {
  return request<StreamStartResponse>("/api/chat/start", {
    method: "POST",
    body: JSON.stringify({
      message,
      session_id: sessionId || undefined,
      user_id: userId,
      model: model || undefined,
    }),
  });
}

export function connectChatStream(streamId: string): EventSource {
  return new EventSource(`${API_BASE}/api/chat/stream?stream_id=${streamId}`);
}

// ── Sessions ──────────────────────────────────────────────────────────────

export function listSessions() {
  return request<{ sessions: SessionCompact[] }>("/api/sessions");
}

export function getSession(sessionId: string) {
  return request<{ session: SessionFull }>(`/api/sessions/${encodeURIComponent(sessionId)}`);
}

export function createSession(title = "New Chat", model?: string) {
  return request<SessionCompact>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ title, model: model || undefined }),
  });
}

export function renameSession(sessionId: string, title: string) {
  return request<SessionCompact>(
    `/api/sessions/${encodeURIComponent(sessionId)}/rename`,
    {
      method: "PUT",
      body: JSON.stringify({ title }),
    }
  );
}

export function deleteSessionApi(sessionId: string) {
  return request<{ deleted: boolean }>(
    `/api/sessions/${encodeURIComponent(sessionId)}`,
    { method: "DELETE" }
  );
}

// ── Memory ────────────────────────────────────────────────────────────────

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

// ── Skills ────────────────────────────────────────────────────────────────

export function listSkills() {
  return request<{ skills: Record<string, unknown>[] }>("/api/skills");
}

export function createSkill(name: string, description: string, code: string) {
  return request<{ saved: boolean; path: string }>("/api/skills", {
    method: "POST",
    body: JSON.stringify({ name, description, code }),
  });
}

export function installSkillFromGitHub(url: string) {
  return request<{ installed: boolean; path: string }>("/api/skills/install", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function deleteSkill(name: string) {
  return request<{ deleted: boolean }>(`/api/skills/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
}

export function listSkillFiles(name: string) {
  return request<{ skill: string; files: { path: string; size: number }[] }>(
    `/api/skills/${encodeURIComponent(name)}/files`
  );
}

export function readSkillFile(name: string, path: string) {
  return request<{ skill: string; path: string; content: string }>(
    `/api/skills/${encodeURIComponent(name)}/file?path=${encodeURIComponent(path)}`
  );
}

// ── Schedules ─────────────────────────────────────────────────────────────

export function listSchedules() {
  return request<{ schedules: Schedule[] }>("/api/schedules");
}

export function createSchedule(data: {
  name: string;
  cron: string;
  description?: string;
  payload?: Record<string, unknown>;
  timezone?: string;
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

// ── Soul ──────────────────────────────────────────────────────────────────

export function getSoul() {
  return request<{ content: string }>("/api/soul");
}

export function updateSoul(content: string) {
  return request<{ saved: boolean }>("/api/soul", {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
}

// ── Channels ──────────────────────────────────────────────────────────────

export function listChannels() {
  return request<{ channels: Channel[] }>("/api/channels");
}

// ── Settings ──────────────────────────────────────────────────────────────

export function getSettings() {
  return request<Settings>("/api/settings");
}

export function updateSettings(data: Partial<Settings>) {
  return request<{ updated: boolean }>("/api/settings", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// ── Health ─────────────────────────────────────────────────────────────────

export function healthCheck() {
  return request<{ status: string; version: string }>("/api/health");
}

// ── Workspaces file browser ────────────────────────────────────────────────

export interface WorkspaceEntry {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number | null;
}

export interface Workspace {
  name: string;
  path: string;
  description: string;
  created_at: number;
}

export function listWorkspaces() {
  return request<{ workspaces: Workspace[] }>("/api/workspaces");
}

export function listWorkspaceFiles(workspaceName: string, path = "") {
  const qs = path ? `?path=${encodeURIComponent(path)}` : "";
  return request<{ workspace: string; path: string; entries: WorkspaceEntry[] }>(
    `/api/workspaces/${encodeURIComponent(workspaceName)}/files${qs}`
  );
}

export function readWorkspaceFile(workspaceName: string, path: string) {
  return request<{ workspace: string; path: string; content: string; size: number }>(
    `/api/workspaces/${encodeURIComponent(workspaceName)}/file?path=${encodeURIComponent(path)}`
  );
}
