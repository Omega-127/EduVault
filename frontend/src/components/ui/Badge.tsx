"use client";

import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "accent" | "danger" | "warning" | "info" | "outline";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-surface-tertiary text-text-secondary",
  accent: "bg-accent-subtle text-accent",
  danger: "bg-danger-subtle text-danger",
  warning: "bg-warning-subtle text-warning",
  info: "bg-info-subtle text-info",
  outline: "bg-transparent border border-border text-text-secondary",
};

export function Badge({
  className,
  variant = "default",
  dot = false,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "badge",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn("w-1.5 h-1.5 rounded-full", {
            "bg-accent": variant === "accent",
            "bg-danger": variant === "danger",
            "bg-warning": variant === "warning",
            "bg-info": variant === "info",
            "bg-text-muted": variant === "default" || variant === "outline",
          })}
        />
      )}
      {children}
    </span>
  );
}
