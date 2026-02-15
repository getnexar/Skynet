"use client";

import { useState } from "react";
import SessionList from "@/components/SessionList";
import ChatView from "@/components/ChatView";
import MessageInput from "@/components/MessageInput";

export default function Home() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  const handleSendMessage = (message: string) => {
    console.log("Message to send:", message);
    // API integration will be implemented later
  };

  return (
    <div className="flex h-screen bg-gray-950 text-white">
      {/* Sidebar - Session List */}
      <div className="w-64 flex-shrink-0">
        <SessionList
          selectedSessionId={selectedSessionId}
          onSelectSession={setSelectedSessionId}
        />
      </div>

      {/* Main Content - Chat View and Input */}
      <div className="flex-1 flex flex-col">
        <ChatView sessionId={selectedSessionId} />
        <MessageInput
          onSend={handleSendMessage}
          disabled={!selectedSessionId}
        />
      </div>
    </div>
  );
}
