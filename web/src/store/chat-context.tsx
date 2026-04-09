"use client";

import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  type ReactNode,
  useEffect,
} from "react";
import {
  type ChatMessage,
  type ToolCallEvent,
  type SessionCompact,
  startChatStream,
  connectChatStream,
  listSessions,
  getSession,
  deleteSessionApi,
  renameSession,
} from "@/lib/api-client";

// ── State ─────────────────────────────────────────────────────────────────

interface ChatState {
  sessions: SessionCompact[];
  currentSessionId: string | null;
  messages: ChatMessage[];
  busy: boolean;
  model: string;
  error: string | null;
  activeTools: ToolCallEvent[];
  streamContent: string;
}

const initialState: ChatState = {
  sessions: [],
  currentSessionId: null,
  messages: [],
  busy: false,
  model: "",
  error: null,
  activeTools: [],
  streamContent: "",
};

// ── Actions ───────────────────────────────────────────────────────────────

type ChatAction =
  | { type: "SET_SESSIONS"; sessions: SessionCompact[] }
  | { type: "SET_CURRENT_SESSION"; sessionId: string | null; messages: ChatMessage[] }
  | { type: "ADD_USER_MESSAGE"; content: string }
  | { type: "SET_BUSY"; busy: boolean }
  | { type: "SET_MODEL"; model: string }
  | { type: "SET_ERROR"; error: string | null }
  | { type: "APPEND_TOKEN"; text: string }
  | { type: "TOOL_START"; tool: ToolCallEvent }
  | { type: "TOOL_END"; name: string; result: string }
  | { type: "STREAM_DONE"; sessionId: string; model: string; title: string }
  | { type: "STREAM_ERROR"; message: string }
  | { type: "CLEAR_MESSAGES" };

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "SET_SESSIONS":
      return { ...state, sessions: action.sessions };

    case "SET_CURRENT_SESSION":
      return {
        ...state,
        currentSessionId: action.sessionId,
        messages: action.messages,
        error: null,
        activeTools: [],
        streamContent: "",
      };

    case "ADD_USER_MESSAGE":
      return {
        ...state,
        messages: [...state.messages, { role: "user", content: action.content }],
        busy: true,
        error: null,
        activeTools: [],
        streamContent: "",
      };

    case "SET_BUSY":
      return { ...state, busy: action.busy };

    case "SET_MODEL":
      return { ...state, model: action.model };

    case "SET_ERROR":
      return { ...state, error: action.error };

    case "APPEND_TOKEN":
      return { ...state, streamContent: state.streamContent + action.text };

    case "TOOL_START":
      return {
        ...state,
        activeTools: [...state.activeTools, action.tool],
      };

    case "TOOL_END":
      return {
        ...state,
        activeTools: state.activeTools.map((t) =>
          t.name === action.name && t.status === "running"
            ? { ...t, status: "completed" as const, result: action.result }
            : t
        ),
      };

    case "STREAM_DONE": {
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: state.streamContent,
        tool_calls:
          state.activeTools.length > 0 ? [...state.activeTools] : undefined,
      };
      return {
        ...state,
        messages: [...state.messages, assistantMsg],
        busy: false,
        streamContent: "",
        activeTools: [],
        model: action.model,
        currentSessionId: action.sessionId,
        sessions: state.sessions.map((s) =>
          s.session_id === action.sessionId
            ? { ...s, title: action.title, message_count: s.message_count + 2 }
            : s
        ),
      };
    }

    case "STREAM_ERROR":
      return {
        ...state,
        messages: [
          ...state.messages,
          {
            role: "assistant",
            content: state.streamContent || `Error: ${action.message}`,
          },
        ],
        busy: false,
        streamContent: "",
        activeTools: [],
        error: action.message,
      };

    case "CLEAR_MESSAGES":
      return {
        ...state,
        messages: [],
        currentSessionId: null,
        activeTools: [],
        streamContent: "",
        error: null,
      };

    default:
      return state;
  }
}

// ── Context ───────────────────────────────────────────────────────────────

interface ChatContextValue {
  state: ChatState;
  sendChat: (message: string) => Promise<void>;
  loadSessions: () => Promise<void>;
  switchSession: (sessionId: string) => Promise<void>;
  newSession: () => void;
  deleteSession: (sessionId: string) => Promise<void>;
  renameSessionAction: (sessionId: string, title: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const loadSessions = useCallback(async () => {
    try {
      const { sessions } = await listSessions();
      dispatch({ type: "SET_SESSIONS", sessions });
    } catch {
      // silent — sessions not available
    }
  }, []);

  const switchSession = useCallback(async (sessionId: string) => {
    try {
      const { session } = await getSession(sessionId);
      const msgs: ChatMessage[] = session.messages.map((m) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
      }));
      dispatch({ type: "SET_CURRENT_SESSION", sessionId, messages: msgs });
    } catch {
      dispatch({ type: "SET_ERROR", error: "Failed to load session" });
    }
  }, []);

  const newSession = useCallback(() => {
    dispatch({ type: "CLEAR_MESSAGES" });
  }, []);

  const deleteSessionAction = useCallback(
    async (sessionId: string) => {
      try {
        await deleteSessionApi(sessionId);
        dispatch({
          type: "SET_SESSIONS",
          sessions: state.sessions.filter((s) => s.session_id !== sessionId),
        });
        if (state.currentSessionId === sessionId) {
          dispatch({ type: "CLEAR_MESSAGES" });
        }
      } catch {
        dispatch({ type: "SET_ERROR", error: "Failed to delete session" });
      }
    },
    [state.sessions, state.currentSessionId]
  );

  const renameSessionAction = useCallback(
    async (sessionId: string, title: string) => {
      try {
        const updated = await renameSession(sessionId, title);
        dispatch({
          type: "SET_SESSIONS",
          sessions: state.sessions.map((s) =>
            s.session_id === sessionId ? { ...s, title: updated.title } : s
          ),
        });
      } catch {
        dispatch({ type: "SET_ERROR", error: "Failed to rename session" });
      }
    },
    [state.sessions]
  );

  const sendChat = useCallback(
    async (message: string) => {
      if (state.busy) return;

      // Handle slash commands
      if (message.startsWith("/")) {
        const cmd = message.split(" ")[0].toLowerCase();
        if (cmd === "/clear") {
          dispatch({ type: "CLEAR_MESSAGES" });
          return;
        }
        if (cmd === "/new") {
          dispatch({ type: "CLEAR_MESSAGES" });
          return;
        }
        if (cmd === "/help") {
          dispatch({ type: "ADD_USER_MESSAGE", content: message });
          dispatch({
            type: "STREAM_DONE",
            sessionId: state.currentSessionId || "",
            model: state.model,
            title: "Help",
          });
          // Insert help message directly
          const helpContent = `## Available Commands

| Command | Description |
|---------|-------------|
| \`/new\` | Start a new chat session |
| \`/clear\` | Clear current chat |
| \`/help\` | Show this help message |

**Keyboard shortcuts:**
- \`Enter\` — Send message
- \`Shift+Enter\` — New line
- \`Ctrl+N\` — New chat`;
          dispatch({
            type: "SET_CURRENT_SESSION",
            sessionId: state.currentSessionId,
            messages: [
              ...state.messages,
              { role: "user", content: message },
              { role: "assistant", content: helpContent },
            ],
          });
          return;
        }
      }

      dispatch({ type: "ADD_USER_MESSAGE", content: message });

      try {
        const { stream_id, session_id: streamSessionId } = await startChatStream(
          message,
          state.currentSessionId || undefined
        );

        const es = connectChatStream(stream_id);

        es.addEventListener("token", (e: MessageEvent) => {
          const data = JSON.parse(e.data);
          dispatch({ type: "APPEND_TOKEN", text: data.text });
        });

        es.addEventListener("tool_start", (e: MessageEvent) => {
          const data = JSON.parse(e.data);
          dispatch({
            type: "TOOL_START",
            tool: { name: data.name, args: data.args, status: "running" },
          });
        });

        es.addEventListener("tool_end", (e: MessageEvent) => {
          const data = JSON.parse(e.data);
          dispatch({ type: "TOOL_END", name: data.name, result: data.result });
        });

        es.addEventListener("done", (e: MessageEvent) => {
          const data = JSON.parse(e.data);
          dispatch({
            type: "STREAM_DONE",
            sessionId: data.session_id || streamSessionId,
            model: data.model || "",
            title: data.title || "Chat",
          });
          es.close();
          loadSessions();
        });

        es.addEventListener("error", (e: MessageEvent) => {
          if (e.data) {
            try {
              const data = JSON.parse(e.data);
              dispatch({ type: "STREAM_ERROR", message: data.message || "Unknown error" });
            } catch {
              dispatch({ type: "STREAM_ERROR", message: "Connection error" });
            }
          } else {
            dispatch({ type: "STREAM_ERROR", message: "Connection lost" });
          }
          es.close();
        });
      } catch (err) {
        dispatch({
          type: "STREAM_ERROR",
          message: err instanceof Error ? err.message : "Failed to start chat",
        });
      }
    },
    [state.busy, state.currentSessionId, state.model, state.messages, loadSessions]
  );

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return (
    <ChatContext.Provider
      value={{
        state,
        sendChat,
        loadSessions,
        switchSession,
        newSession,
        deleteSession: deleteSessionAction,
        renameSessionAction,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
