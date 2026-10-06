"use client";

import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { SessionSidebar } from "@/components/chat/SessionSidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChat, useChatSessions } from "@/hooks/useChat";

/**
 * Active chat session page.
 * Renders the full chat UI with message history, streaming, and input.
 */
export default function ChatSessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const { sessions, isLoading: sessionsLoading, createSession } = useChatSessions();
  const {
    messages,
    streaming,
    isLoadingHistory,
    error,
    ask,
    clearError,
  } = useChat(sessionId);

  const handleCreateSession = async () => {
    try {
      const session = await createSession();
      router.push(`/chat/${session.id}`);
    } catch {
      // Handle error silently
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar />

      <div className="flex flex-1 overflow-hidden">
        {/* Session sidebar */}
        <SessionSidebar
          sessions={sessions}
          isLoading={sessionsLoading}
          onCreateSession={handleCreateSession}
        />

        {/* Chat window */}
        <div className="flex-1">
          <ChatWindow
            messages={messages}
            streaming={streaming}
            isLoadingHistory={isLoadingHistory}
            error={error}
            onSend={ask}
            onClearError={clearError}
          />
        </div>
      </div>
    </div>
  );
}
