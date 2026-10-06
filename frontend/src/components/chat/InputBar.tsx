"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Paperclip } from "lucide-react";
import { cn } from "@/lib/utils";

interface InputBarProps {
  onSend: (message: string) => void;
  isDisabled?: boolean;
  isStreaming?: boolean;
  placeholder?: string;
  className?: string;
}

/**
 * Chat input bar with auto-resize textarea, send button, and keyboard shortcut.
 * Enter sends the message, Shift+Enter adds a new line.
 */
export function InputBar({
  onSend,
  isDisabled = false,
  isStreaming = false,
  placeholder = "Ask a question about university policies...",
  className,
}: InputBarProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize the textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    }
  }, [message]);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || isDisabled || isStreaming) return;

    onSend(trimmed);
    setMessage("");

    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className={cn(
        "flex items-end gap-3 p-4 border-t border-border bg-surface-primary",
        className
      )}
    >
      {/* Attachment button (future) */}
      <button
        className="flex-shrink-0 p-2.5 rounded-lg text-text-muted
                   hover:text-text-primary hover:bg-surface-tertiary
                   transition-colors duration-200"
        title="Attach file"
        disabled
      >
        <Paperclip className="w-5 h-5" />
      </button>

      {/* Text input */}
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isDisabled}
          rows={1}
          className="input-base resize-none pr-4 min-h-[44px] max-h-[160px]"
        />
      </div>

      {/* Send button */}
      <button
        onClick={handleSend}
        disabled={!message.trim() || isDisabled || isStreaming}
        className={cn(
          "flex-shrink-0 flex items-center justify-center",
          "w-11 h-11 rounded-lg transition-all duration-200",
          message.trim() && !isDisabled && !isStreaming
            ? "bg-accent text-text-inverse hover:bg-accent-hover shadow-card"
            : "bg-surface-tertiary text-text-muted cursor-not-allowed"
        )}
        title="Send message (Enter)"
      >
        <Send className="w-5 h-5" />
      </button>
    </div>
  );
}
