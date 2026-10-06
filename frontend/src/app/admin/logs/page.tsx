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
  AlertCircle,
  Info,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Filter,
} from "lucide-react";

interface SystemLog {
  id: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

const eventTypeConfig: Record<
  string,
  { icon: React.ElementType; variant: "danger" | "warning" | "info" | "accent"; label: string }
> = {
  unanswerable_query: {
    icon: AlertTriangle,
    variant: "warning",
    label: "Unanswerable",
  },
  ingestion_failed: {
    icon: AlertCircle,
    variant: "danger",
    label: "Ingestion Failed",
  },
  ingestion_complete: {
    icon: CheckCircle,
    variant: "accent",
    label: "Ingested",
  },
  user_registered: {
    icon: Info,
    variant: "info",
    label: "Registration",
  },
};

const defaultConfig = {
  icon: Info,
  variant: "info" as const,
  label: "Event",
};

export default function AdminLogsPage() {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  const loadLogs = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await api.get<SystemLog[]>("/admin/logs");
      setLogs(data);
    } catch {
      // Handle error
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const filteredLogs =
    filter === "all"
      ? logs
      : logs.filter((log) => log.event_type === filter);

  const eventTypes = [...new Set(logs.map((l) => l.event_type))];

  return (
    <div className="flex h-screen">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          title="System Logs"
          subtitle={`${logs.length} events recorded`}
          actions={
            <Button
              size="sm"
              variant="ghost"
              onClick={loadLogs}
              leftIcon={<RefreshCw className="w-4 h-4" />}
            >
              Refresh
            </Button>
          }
        />

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Filters */}
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="w-4 h-4 text-text-muted" />
            <button
              onClick={() => setFilter("all")}
              className={`badge ${
                filter === "all"
                  ? "bg-accent text-text-inverse"
                  : "bg-surface-tertiary text-text-secondary hover:text-text-primary"
              } cursor-pointer transition-colors`}
            >
              All
            </button>
            {eventTypes.map((type) => {
              const config = eventTypeConfig[type] || defaultConfig;
              return (
                <button
                  key={type}
                  onClick={() => setFilter(type)}
                  className={`badge cursor-pointer transition-colors ${
                    filter === type
                      ? "bg-accent text-text-inverse"
                      : "bg-surface-tertiary text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {config.label}
                </button>
              );
            })}
          </div>

          {/* Log entries */}
          <div className="card p-0 overflow-hidden">
            {isLoading ? (
              <div className="flex items-center justify-center py-16">
                <Spinner size="lg" />
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Info className="w-8 h-8 text-text-muted mb-3" />
                <p className="text-sm text-text-muted">No log entries found</p>
              </div>
            ) : (
              <div className="divide-y divide-border/50">
                {filteredLogs.map((log) => {
                  const config = eventTypeConfig[log.event_type] || defaultConfig;
                  const Icon = config.icon;

                  return (
                    <div
                      key={log.id}
                      className="flex items-start gap-4 px-6 py-4 hover:bg-surface-tertiary/30 transition-colors"
                    >
                      {/* Icon */}
                      <div className="mt-0.5">
                        <Badge variant={config.variant}>
                          <Icon className="w-3 h-3" />
                        </Badge>
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-text-primary">
                            {config.label}
                          </span>
                          <span className="text-2xs text-text-muted font-mono">
                            {log.event_type}
                          </span>
                        </div>

                        {/* Payload preview */}
                        {log.payload && Object.keys(log.payload).length > 0 && (
                          <pre className="text-xs text-text-muted font-mono bg-surface-primary rounded-lg p-2 overflow-x-auto max-h-24">
                            {JSON.stringify(log.payload, null, 2)}
                          </pre>
                        )}
                      </div>

                      {/* Timestamp */}
                      <span className="text-xs text-text-muted whitespace-nowrap flex-shrink-0">
                        {formatDate(log.created_at)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
