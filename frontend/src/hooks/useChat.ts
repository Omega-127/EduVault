"use client";

import { useState, useCallback, useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import api from "@/lib/api";
import type { Message, Citation, StreamingMessage, ChatSession } from "@/types/chat";

interface AskResponse {
  user_message: Message;
  assistant_message: Message;
}

/**
 * Chat hook — sends questions over HTTP (reliable) and manages message state.
 */
export function useChat(sessionId: string | null) {
  const { accessToken } = useAuthStore();

  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState<StreamingMessage>({
    content: "",
    citations: [],
    isStreaming: false,
  });
  const [isConnected, setIsConnected] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getToken = useCallback(() => {
    return (
      accessToken ||
      (typeof window !== "undefined"
        ? localStorage.getItem("access_token")
        : null)
    );
  }, [accessToken]);

  /** Load message history for the session */
  const loadHistory = useCallback(async () => {
    if (!sessionId) return;

    setIsLoadingHistory(true);
    try {
      const { data } = await api.get<Message[]>(
        `/chat/sessions/${sessionId}/messages`
      );
      setMessages(
        data.map((m) => ({
          ...m,
          citations: (m.citations || []) as Citation[],
        }))
      );
      setIsConnected(true);
      setError(null);
    } catch {
      setIsConnected(false);
      setError("Failed to load chat history. Is the backend running?");
    } finally {
      setIsLoadingHistory(false);
    }
  }, [sessionId]);

  /** Send a question via HTTP */
  const ask = useCallback(
    async (question: string) => {
      const token = getToken();

      if (!token) {
        setError(
          "You must be logged in to send messages. Please log in at /login."
        );
        return;
      }

      if (!sessionId) {
        setError("No active chat session. Please start a new chat.");
        return;
      }

      const trimmed = question.trim();
      if (!trimmed) return;

      const optimisticUser: Message = {
        id: `local-${Date.now()}`,
        session_id: sessionId,
        role: "user",
        content: trimmed,
        citations: [],
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, optimisticUser]);
      setStreaming({ content: "", citations: [], isStreaming: true });
      setError(null);

      try {
        const { data } = await api.post<AskResponse>(
          `/chat/sessions/${sessionId}/ask`,
          { question: trimmed },
          { timeout: 120000 }
        );

        const userMsg: Message = {
          ...data.user_message,
          citations: (data.user_message.citations || []) as Citation[],
        };
        const asstMsg: Message = {
          ...data.assistant_message,
          citations: (data.assistant_message.citations || []) as Citation[],
        };

        setMessages((prev) => {
          const withoutOptimistic = prev.filter((m) => m.id !== optimisticUser.id);
          return [...withoutOptimistic, userMsg, asstMsg];
        });
        setStreaming({ content: "", citations: [], isStreaming: false });
        setIsConnected(true);
      } catch (err: unknown) {
        setMessages((prev) => prev.filter((m) => m.id !== optimisticUser.id));
        setStreaming({ content: "", citations: [], isStreaming: false });
        setIsConnected(false);

        const axiosErr = err as {
          response?: { data?: { detail?: string }; status?: number };
          code?: string;
          message?: string;
        };
        const detail = axiosErr.response?.data?.detail;
        if (typeof detail === "string") {
          setError(detail);
        } else if (
          axiosErr.code === "ERR_NETWORK" ||
          axiosErr.message?.includes("Network Error")
        ) {
          setError(
            "Cannot reach the backend at localhost:8000. Start the FastAPI server and try again."
          );
        } else {
          setError("Failed to send message. Please try again.");
        }
      }
    },
    [sessionId, getToken]
  );

  useEffect(() => {
    if (sessionId) {
      loadHistory();
    }
  }, [sessionId, loadHistory]);

  return {
    messages,
    streaming,
    isConnected,
    isLoadingHistory,
    error,
    ask,
    clearError: () => setError(null),
  };
}

/**
 * Hook to manage chat sessions (list, create, delete).
 */
export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadSessions = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<ChatSession[]>("/chat/sessions");
      setSessions(data);
    } catch {
      // Silently fail — sessions will show empty
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createSession = useCallback(async (title?: string) => {
    const { data } = await api.post<ChatSession>("/chat/sessions", {
      title: title || "New Chat",
    });
    setSessions((prev) => [data, ...prev]);
    return data;
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return { sessions, isLoading, createSession, refreshSessions: loadSessions };
}
