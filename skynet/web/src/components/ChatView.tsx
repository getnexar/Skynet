"use client";

import { useState, useEffect, useRef } from "react";
import { ChevronDown, ChevronRight, Terminal } from "lucide-react";
import { format } from "date-fns";

interface ToolCall {
  name: string;
  input: Record<string, unknown>;
  output?: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  tool_calls?: ToolCall[];
  timestamp: string;
}

interface ChatViewProps {
  sessionId: string | null;
}

function ToolCallItem({ toolCall }: { toolCall: ToolCall }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-2 border border-gray-700 rounded-md overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 p-2 bg-gray-800 hover:bg-gray-750 transition-colors text-left"
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
        <Terminal className="w-4 h-4 text-purple-400" />
        <span className="text-sm text-purple-400 font-mono">{toolCall.name}</span>
      </button>
      {expanded && (
        <div className="p-3 bg-gray-850 text-xs font-mono">
          <div className="mb-2">
            <span className="text-gray-500">Input:</span>
            <pre className="mt-1 p-2 bg-gray-900 rounded text-gray-300 overflow-x-auto">
              {JSON.stringify(toolCall.input, null, 2)}
            </pre>
          </div>
          {toolCall.output && (
            <div>
              <span className="text-gray-500">Output:</span>
              <pre className="mt-1 p-2 bg-gray-900 rounded text-gray-300 overflow-x-auto whitespace-pre-wrap">
                {toolCall.output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MessageItem({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const timestamp = format(new Date(message.timestamp), "HH:mm");

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] ${
          isUser ? "bg-blue-600" : "bg-gray-800"
        } rounded-lg p-3`}
      >
        <div className="text-white whitespace-pre-wrap">{message.content}</div>
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div className="mt-2">
            {message.tool_calls.map((toolCall, index) => (
              <ToolCallItem key={index} toolCall={toolCall} />
            ))}
          </div>
        )}
        <div
          className={`text-xs mt-2 ${
            isUser ? "text-blue-200" : "text-gray-500"
          }`}
        >
          {timestamp}
        </div>
      </div>
    </div>
  );
}

export default function ChatView({ sessionId }: ChatViewProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prevMessageCountRef = useRef(0);

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }

    const fetchMessages = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `http://localhost:8000/api/sessions/${sessionId}/messages`
        );
        if (!response.ok) {
          throw new Error("Failed to fetch messages");
        }
        const data = await response.json();
        setMessages(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch messages");
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [sessionId]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > prevMessageCountRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
    prevMessageCountRef.current = messages.length;
  }, [messages]);

  if (!sessionId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-950">
        <p className="text-gray-500">Select a session to view messages</p>
      </div>
    );
  }

  if (loading && messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-950">
        <p className="text-gray-400">Loading messages...</p>
      </div>
    );
  }

  if (error && messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-950">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-gray-950 p-4">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500">No messages yet</p>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageItem key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  );
}
