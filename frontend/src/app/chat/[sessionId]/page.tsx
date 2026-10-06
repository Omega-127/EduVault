"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { SessionSidebar } from "@/components/chat/SessionSidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChat, useChatSessions } from "@/hooks/useChat";
import { useDocuments } from "@/hooks/useDocuments";

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

  const { uploadDocument, isUploading: isUploadingDoc } = useDocuments();
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const handleAttachFile = async (file: File) => {
    setUploadStatus(`Uploading "${file.name}" to knowledge base...`);
    const res = await uploadDocument(file);
    if (res) {
      setUploadStatus(`"${file.name}" uploaded successfully! Indexing into knowledge base...`);
      setTimeout(() => setUploadStatus(null), 5000);
    } else {
      setUploadStatus(`Failed to upload "${file.name}". Please try again.`);
      setTimeout(() => setUploadStatus(null), 6000);
    }
  };

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
            onAttachFile={handleAttachFile}
            isUploadingFile={isUploadingDoc}
            uploadStatusMessage={uploadStatus}
            onClearError={clearError}
          />
        </div>
      </div>
    </div>
  );
}
