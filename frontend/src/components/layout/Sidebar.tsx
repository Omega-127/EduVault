"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  FileText,
  Users,
  ScrollText,
  ChevronLeft,
  ChevronRight,
  Shield,
  GraduationCap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";

const mainNavItems = [
  {
    label: "Chat",
    href: "/chat",
    icon: MessageSquare,
  },
];

const adminNavItems = [
  {
    label: "Documents",
    href: "/admin/documents",
    icon: FileText,
  },
  {
    label: "Users",
    href: "/admin/users",
    icon: Users,
  },
  {
    label: "Logs",
    href: "/admin/logs",
    icon: ScrollText,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, isAdmin, logout } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-surface-secondary border-r border-border",
        "transition-all duration-300 ease-out",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-border">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent">
          <GraduationCap className="w-5 h-5 text-text-inverse" />
        </div>
        {!isCollapsed && (
          <span className="text-lg font-bold text-text-primary tracking-tight">
            EduVault
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {/* Main nav */}
        {mainNavItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn("sidebar-link", isActive && "active")}
              title={isCollapsed ? item.label : undefined}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!isCollapsed && <span>{item.label}</span>}
            </Link>
          );
        })}

        {/* Admin section */}
        {isAdmin && (
          <>
            <div className="pt-4 pb-2">
              {!isCollapsed && (
                <div className="flex items-center gap-2 px-3">
                  <Shield className="w-3.5 h-3.5 text-accent" />
                  <span className="text-2xs font-semibold text-text-muted uppercase tracking-widest">
                    Admin
                  </span>
                </div>
              )}
              {isCollapsed && (
                <div className="w-8 mx-auto border-t border-border" />
              )}
            </div>
            {adminNavItems.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn("sidebar-link", isActive && "active")}
                  title={isCollapsed ? item.label : undefined}
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  {!isCollapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </>
        )}
      </nav>

      {/* User section */}
      <div className="border-t border-border p-3 space-y-2">
        {user && !isCollapsed && (
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-surface-tertiary text-text-secondary text-xs font-semibold">
              {user.email.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {user.email}
              </p>
              <p className="text-2xs text-text-muted capitalize">{user.role}</p>
            </div>
          </div>
        )}

        <button
          onClick={logout}
          className={cn(
            "sidebar-link text-danger hover:bg-danger-subtle hover:text-danger w-full",
            isCollapsed && "justify-center"
          )}
        >
          {!isCollapsed && <span>Sign Out</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setIsCollapsed((c) => !c)}
        className="flex items-center justify-center h-10 border-t border-border
                   text-text-muted hover:text-text-primary hover:bg-surface-tertiary
                   transition-colors duration-200"
      >
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4" />
        ) : (
          <ChevronLeft className="w-4 h-4" />
        )}
      </button>
    </aside>
  );
}
