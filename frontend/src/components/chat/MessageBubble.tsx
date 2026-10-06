"use client";

import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils";
import { CitationBadge } from "./CitationBadge";
import { User, Bot } from "lucide-react";
import type { Message, Citation } from "@/types/chat";

interface MessageBubbleProps {
  message: Message;
  onCitationClick?: (citation: Citation) => void;
  className?: string;
}

/**
 * Renders a single chat message with content and interactive citation badges.
 * User messages align right, assistant messages align left.
 */
export function MessageBubble({
  message,
  onCitationClick,
  className,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 animate-slide-up",
        isUser ? "flex-row-reverse" : "flex-row",
        className
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex items-center justify-center w-8 h-8 rounded-lg flex-shrink-0 mt-1",
          isUser
            ? "bg-surface-tertiary text-text-secondary"
            : "bg-accent text-text-inverse"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message content */}
      <div
        className={cn(
          "max-w-[75%] space-y-2",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "px-4 py-3 rounded-2xl text-sm leading-relaxed",
            isUser
              ? "bg-accent text-text-inverse rounded-tr-md"
              : "bg-surface-secondary border border-border text-text-primary rounded-tl-md"
          )}
        >
          <div className="whitespace-pre-wrap break-words">
            {message.content}
          </div>
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-1 pt-1">
            {message.citations.map((citation, idx) => (
              <CitationBadge
                key={idx}
                citation={citation}
                onClick={onCitationClick}
              />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p
          className={cn(
            "text-2xs text-text-muted px-1",
            isUser ? "text-right" : "text-left"
          )}
        >
          {formatDate(message.created_at)}
        </p>
      </div>
    </div>
  );
}
