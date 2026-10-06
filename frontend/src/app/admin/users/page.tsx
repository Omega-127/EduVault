"use client";

import { useState, useEffect, useCallback } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate } from "@/lib/utils";
import api from "@/lib/api";
import {
  Users,
  Shield,
  GraduationCap,
  BookOpen,
  MoreHorizontal,
} from "lucide-react";
import type { User } from "@/types/user";

const roleConfig = {
  admin: {
    icon: Shield,
    variant: "danger" as const,
    color: "text-danger",
  },
  faculty: {
    icon: BookOpen,
    variant: "warning" as const,
    color: "text-warning",
  },
  student: {
    icon: GraduationCap,
    variant: "accent" as const,
    color: "text-accent",
  },
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<User[]>("/admin/users");
      setUsers(data);
    } catch {
      // Handle error
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Stats
  const stats = {
    total: users.length,
    students: users.filter((u) => u.role === "student").length,
    faculty: users.filter((u) => u.role === "faculty").length,
    admins: users.filter((u) => u.role === "admin").length,
  };

  return (
    <div className="flex h-screen">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          title="User Management"
          subtitle={`${stats.total} registered users`}
        />

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Stats cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                label: "Total Users",
                value: stats.total,
                icon: Users,
                color: "text-text-primary",
                bg: "bg-surface-tertiary",
              },
              {
                label: "Students",
                value: stats.students,
                icon: GraduationCap,
                color: "text-accent",
                bg: "bg-accent-subtle",
              },
              {
                label: "Faculty",
                value: stats.faculty,
                icon: BookOpen,
                color: "text-warning",
                bg: "bg-warning-subtle",
              },
              {
                label: "Admins",
                value: stats.admins,
                icon: Shield,
                color: "text-danger",
                bg: "bg-danger-subtle",
              },
            ].map((stat, idx) => (
              <div key={idx} className="card p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-text-muted">{stat.label}</span>
                  <div
                    className={`w-8 h-8 rounded-lg ${stat.bg} flex items-center justify-center`}
                  >
                    <stat.icon className={`w-4 h-4 ${stat.color}`} />
                  </div>
                </div>
                <p className="text-2xl font-bold text-text-primary">
                  {stat.value}
                </p>
              </div>
            ))}
          </div>

          {/* Users table */}
          <div className="card p-0 overflow-hidden">
            <div className="px-6 py-4 border-b border-border">
              <h2 className="text-base font-semibold text-text-primary">
                All Users
              </h2>
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-16">
                <Spinner size="lg" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="table-header">User</th>
                      <th className="table-header">Role</th>
                      <th className="table-header">Status</th>
                      <th className="table-header">Joined</th>
                      <th className="table-header text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => {
                      const config = roleConfig[user.role];
                      const RoleIcon = config.icon;

                      return (
                        <tr key={user.id} className="table-row">
                          <td className="table-cell">
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 rounded-full bg-surface-tertiary flex items-center justify-center text-xs font-semibold text-text-secondary">
                                {user.email.slice(0, 2).toUpperCase()}
                              </div>
                              <span className="text-sm font-medium text-text-primary">
                                {user.email}
                              </span>
                            </div>
                          </td>
                          <td className="table-cell">
                            <Badge variant={config.variant} dot>
                              <RoleIcon className="w-3 h-3" />
                              {user.role}
                            </Badge>
                          </td>
                          <td className="table-cell">
                            <Badge
                              variant={user.is_active ? "accent" : "default"}
                              dot
                            >
                              {user.is_active ? "Active" : "Inactive"}
                            </Badge>
                          </td>
                          <td className="table-cell">
                            <span className="text-sm text-text-muted">
                              {formatDate(user.created_at)}
                            </span>
                          </td>
                          <td className="table-cell text-right">
                            <Button
                              size="icon"
                              variant="ghost"
                              className="w-8 h-8"
                            >
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
