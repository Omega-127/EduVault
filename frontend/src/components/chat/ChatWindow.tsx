"use client";

import { useRef, useEffect } from "react";
import { MessageBubble } from "./MessageBubble";
import { InputBar } from "./InputBar";
import { TypingIndicator } from "@/components/ui/Spinner";
import { Spinner } from "@/components/ui/Spinner";
import { Bot, GraduationCap, BookOpen, Search, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Message, StreamingMessage } from "@/types/chat";

interface ChatWindowProps {
  messages: Message[];
  streaming: StreamingMessage;
  isLoadingHistory: boolean;
  error: string | null;
  onSend: (message: string) => void;
  onClearError?: () => void;
  className?: string;
}

/**
 * Main chat window — renders message list, streaming state, and input bar.
 * Auto-scrolls to the latest message.
 */
export function ChatWindow({
  messages,
  streaming,
  isLoadingHistory,
  error,
  onSend,
  onClearError,
  className,
}: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll when messages change or during streaming
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streaming.content]);

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Message area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-6 space-y-6"
      >
        {/* Loading history */}
        {isLoadingHistory && (
          <div className="flex items-center justify-center py-8">
            <Spinner size="lg" />
          </div>
        )}

        {/* Empty state */}
        {!isLoadingHistory && messages.length === 0 && !streaming.isStreaming && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-16 h-16 rounded-2xl bg-accent-subtle flex items-center justify-center mb-6">
              <GraduationCap className="w-8 h-8 text-accent" />
            </div>
            <h2 className="text-xl font-semibold text-text-primary mb-2">
              Ask EduVault Anything
            </h2>
            <p className="text-sm text-text-muted max-w-md mb-8">
              Get instant, source-grounded answers from your university&apos;s
              official documents, policies, and circulars.
            </p>

            {/* Suggested prompts */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              {[
                {
                  icon: BookOpen,
                  text: "What is the minimum attendance to sit for exams?",
                },
                {
                  icon: FileText,
                  text: "When is the last date to apply for re-evaluation?",
                },
                {
                  icon: Search,
                  text: "Which scholarships require a minimum CGPA of 8.0?",
                },
                {
                  icon: GraduationCap,
                  text: "What are the eligibility criteria for academic probation?",
                },
              ].map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => onSend(prompt.text)}
                  className="flex items-start gap-3 p-3.5 rounded-xl text-left
                             bg-surface-secondary border border-border
                             hover:border-accent/30 hover:bg-surface-tertiary
                             transition-all duration-200 group"
                >
                  <prompt.icon className="w-4 h-4 text-text-muted mt-0.5 group-hover:text-accent transition-colors" />
                  <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">
                    {prompt.text}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {/* Streaming assistant message */}
        {streaming.isStreaming && (
          <div className="flex gap-3 animate-fade-in">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent text-text-inverse flex-shrink-0 mt-1">
              <Bot className="w-4 h-4" />
            </div>
            <div className="max-w-[75%] space-y-2">
              <div className="px-4 py-3 rounded-2xl rounded-tl-md bg-surface-secondary border border-border">
                {streaming.content ? (
                  <div className="text-sm text-text-primary whitespace-pre-wrap break-words leading-relaxed">
                    {streaming.content}
                    <span className="inline-block w-2 h-4 ml-1 bg-accent animate-pulse rounded-sm" />
                  </div>
                ) : (
                  <TypingIndicator />
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-danger-subtle border border-danger/20 text-danger text-sm animate-slide-up">
              <span>{error}</span>
              {onClearError && (
                <button
                  onClick={onClearError}
                  className="text-xs underline hover:no-underline"
                >
                  Dismiss
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Input bar */}
      <InputBar onSend={onSend} isStreaming={streaming.isStreaming} />
    </div>
  );
}
