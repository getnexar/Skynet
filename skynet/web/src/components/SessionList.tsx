"use client";

import { useState, useEffect } from "react";
import { Circle, CheckCircle, AlertCircle, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Session {
  id: string;
  project_path: string;
  status: "running" | "completed" | "failed";
  created_at: string;
  updated_at: string;
}

interface SessionListProps {
  selectedSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
}

type FilterType = "all" | "running" | "completed";

export default function SessionList({
  selectedSessionId,
  onSelectSession,
}: SessionListProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [filter, setFilter] = useState<FilterType>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/sessions");
        if (!response.ok) {
          throw new Error("Failed to fetch sessions");
        }
        const data = await response.json();
        setSessions(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch sessions");
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  const getProjectName = (path: string): string => {
    const parts = path.split("/");
    return parts[parts.length - 1] || path;
  };

  const getStatusIcon = (status: Session["status"]) => {
    switch (status) {
      case "running":
        return <Circle className="w-4 h-4 text-green-500 fill-green-500" />;
      case "completed":
        return <CheckCircle className="w-4 h-4 text-gray-400" />;
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Circle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTimeAgo = (dateString: string): string => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return "unknown";
    }
  };

  const filteredSessions = sessions.filter((session) => {
    if (filter === "all") return true;
    if (filter === "running") return session.status === "running";
    if (filter === "completed")
      return session.status === "completed" || session.status === "failed";
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-gray-900 border-r border-gray-800">
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-3">Sessions</h2>
        <div className="flex gap-1">
          {(["all", "running", "completed"] as FilterType[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-sm rounded-md capitalize transition-colors ${
                filter === f
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center p-4">
            <Clock className="w-5 h-5 text-gray-400 animate-spin" />
            <span className="ml-2 text-gray-400">Loading...</span>
          </div>
        ) : error ? (
          <div className="p-4 text-red-400 text-sm">{error}</div>
        ) : filteredSessions.length === 0 ? (
          <div className="p-4 text-gray-500 text-sm">No sessions found</div>
        ) : (
          <ul className="divide-y divide-gray-800">
            {filteredSessions.map((session) => (
              <li key={session.id}>
                <button
                  onClick={() => onSelectSession(session.id)}
                  className={`w-full p-3 text-left transition-colors ${
                    selectedSessionId === session.id
                      ? "bg-blue-900/30 border-l-2 border-blue-500"
                      : "hover:bg-gray-800"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {getStatusIcon(session.status)}
                    <span className="text-white font-medium truncate">
                      {getProjectName(session.project_path)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 pl-6">
                    {getTimeAgo(session.updated_at)}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
