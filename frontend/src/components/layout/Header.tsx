"use client";

import { Bell, Search } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function Header({ title, subtitle, actions, className }: HeaderProps) {
  return (
    <header
      className={cn(
        "flex items-center justify-between px-6 h-16 border-b border-border",
        "bg-surface-primary",
        className
      )}
    >
      <div>
        <h1 className="text-lg font-semibold text-text-primary">{title}</h1>
        {subtitle && (
          <p className="text-sm text-text-muted">{subtitle}</p>
        )}
      </div>

      <div className="flex items-center gap-2">
        {actions}
        <button
          className="p-2 rounded-lg text-text-muted hover:text-text-primary
                     hover:bg-surface-tertiary transition-colors duration-200"
        >
          <Search className="w-5 h-5" />
        </button>
        <button
          className="relative p-2 rounded-lg text-text-muted hover:text-text-primary
                     hover:bg-surface-tertiary transition-colors duration-200"
        >
          <Bell className="w-5 h-5" />
          {/* Notification dot */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-accent" />
        </button>
      </div>
    </header>
  );
}
