"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Plus, MessageSquare } from "lucide-react";
import { cn, formatDate, truncate } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import type { ChatSession } from "@/types/chat";

interface SessionSidebarProps {
  sessions: ChatSession[];
  isLoading: boolean;
  onCreateSession: () => void;
  className?: string;
}

/**
 * Left-side panel inside the chat page showing all chat sessions.
 */
export function SessionSidebar({
  sessions,
  isLoading,
  onCreateSession,
  className,
}: SessionSidebarProps) {
  const pathname = usePathname();

  return (
    <div
      className={cn(
        "flex flex-col w-72 border-r border-border bg-surface-secondary/50 h-full",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h2 className="text-sm font-semibold text-text-primary">
          Conversations
        </h2>
        <Button
          size="sm"
          variant="ghost"
          onClick={onCreateSession}
          leftIcon={<Plus className="w-4 h-4" />}
          className="text-accent hover:text-accent-hover"
        >
          New
        </Button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Spinner size="sm" />
          </div>
        )}

        {!isLoading && sessions.length === 0 && (
          <div className="text-center py-8 px-4">
            <MessageSquare className="w-8 h-8 text-text-muted mx-auto mb-2" />
            <p className="text-sm text-text-muted">No conversations yet</p>
            <p className="text-xs text-text-muted mt-1">
              Start a new chat to get answers
            </p>
          </div>
        )}

        {sessions.map((session) => {
          const isActive = pathname === `/chat/${session.id}`;
          return (
            <Link
              key={session.id}
              href={`/chat/${session.id}`}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg",
                "transition-all duration-200",
                isActive
                  ? "bg-accent-subtle text-accent border border-accent/20"
                  : "text-text-secondary hover:bg-surface-tertiary hover:text-text-primary"
              )}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {truncate(session.title, 28)}
                </p>
                <p className="text-2xs text-text-muted">
                  {formatDate(session.updated_at)}
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
