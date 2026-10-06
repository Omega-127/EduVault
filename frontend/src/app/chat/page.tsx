"use client";

import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { SessionSidebar } from "@/components/chat/SessionSidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChatSessions } from "@/hooks/useChat";
import { GraduationCap, MessageSquare, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";

/**
 * Chat landing page — shows session list.
 * When no session is selected, shows a welcome state prompting to start a new chat.
 */
export default function ChatPage() {
  const router = useRouter();
  const { sessions, isLoading, createSession } = useChatSessions();

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
          isLoading={isLoading}
          onCreateSession={handleCreateSession}
        />

        {/* Main area — welcome/empty state */}
        <div className="flex-1 flex flex-col items-center justify-center bg-surface-primary px-8">
          <div className="max-w-md text-center space-y-6">
            <div className="w-20 h-20 rounded-2xl bg-accent-subtle flex items-center justify-center mx-auto">
              <GraduationCap className="w-10 h-10 text-accent" />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-text-primary mb-2">
                Welcome to EduVault
              </h1>
              <p className="text-sm text-text-muted leading-relaxed">
                Your AI-powered university knowledge assistant. Ask questions
                about policies, regulations, schedules, and more — with answers
                grounded in official institutional documents.
              </p>
            </div>

            <Button
              size="lg"
              onClick={handleCreateSession}
              leftIcon={<MessageSquare className="w-5 h-5" />}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Start a New Chat
            </Button>

            <div className="flex items-center justify-center gap-6 pt-4">
              {[
                { count: sessions.length, label: "Conversations" },
                { count: "4", label: "Doc Formats" },
                { count: "∞", label: "Questions" },
              ].map((stat, idx) => (
                <div key={idx} className="text-center">
                  <p className="text-lg font-bold text-text-primary">
                    {stat.count}
                  </p>
                  <p className="text-2xs text-text-muted">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
