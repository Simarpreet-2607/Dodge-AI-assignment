import { useState, useRef, useEffect } from "react";
import { ApiClient } from "@/lib/api";
import { ChatMessage, QueryResponse } from "@/types";

interface ChatPanelProps {
  onHighlightNodes: (nodeIds: string[]) => void;
}

export default function ChatPanel({ onHighlightNodes }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedQueries = [
    "Which products have the highest number of invoices?",
    "Trace the full flow of a billing document",
    "Find orders that were delivered but not billed",
    "Show me the delivery status for the most expensive order"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (msg: string) => {
    if (!msg.trim() || isLoading) return;

    const userMessage = msg.trim();
    setInputMessage("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const response: QueryResponse = await ApiClient.postQuery(userMessage, history);
      
      setMessages((prev) => [
        ...prev,
        { 
          role: "assistant", 
          content: response.answer,
          isError: !response.is_data_query
        }
      ]);

      if (response.highlighted_nodes && response.highlighted_nodes.length > 0) {
        onHighlightNodes(response.highlighted_nodes);
      } else {
        onHighlightNodes([]);
      }
    } catch (error: any) {
      setMessages((prev) => [
        ...prev,
        { 
          role: "assistant", 
          content: error.message || "An error occurred while processing your query.", 
          isError: true 
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(inputMessage);
  };

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", background: "var(--panel-bg)", borderLeft: "1px solid var(--panel-border)" }}>
      {/* Header */}
      <div style={{ padding: "16px", borderBottom: "1px solid var(--panel-border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h2 style={{ fontSize: "16px", fontWeight: "600", margin: 0 }}>Data Explorer Assistant</h2>
      </div>

      {/* Message List */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px", display: "flex", flexDirection: "column", gap: "16px" }}>
        {messages.length === 0 ? (
          <div style={{ margin: "auto", textAlign: "center", color: "#94a3b8" }}>
            <p>Ask a question in natural language about your data.</p>
            <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
              {suggestedQueries.map((query, index) => (
                <button 
                  key={index}
                  onClick={() => handleSendMessage(query)}
                  style={{
                    padding: "8px 12px",
                    background: "rgba(59, 130, 246, 0.1)",
                    border: "1px solid var(--primary)",
                    color: "var(--primary)",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontSize: "14px",
                    transition: "all 0.2s"
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.background = "rgba(59, 130, 246, 0.2)")}
                  onMouseOut={(e) => (e.currentTarget.style.background = "rgba(59, 130, 246, 0.1)")}
                >
                  {query}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} style={{
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "85%",
              padding: "12px 16px",
              borderRadius: "12px",
              borderTopRightRadius: msg.role === "user" ? "4px" : "12px",
              borderTopLeftRadius: msg.role === "assistant" ? "4px" : "12px",
              background: msg.role === "user" ? "var(--chat-user-bg)" : "var(--chat-ai-bg)",
              color: msg.role === "user" ? "var(--chat-user-text)" : (msg.isError ? "#ef4444" : "var(--chat-ai-text)"),
              border: msg.role === "assistant" && msg.isError ? "1px solid #7f1d1d" : "none",
              boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
              lineHeight: 1.5,
              fontSize: "14px",
              whiteSpace: "pre-wrap"
            }}>
              {msg.content}
            </div>
          ))
        )}
        
        {isLoading && (
          <div style={{ alignSelf: "flex-start", padding: "12px 16px", borderRadius: "12px", background: "var(--chat-ai-bg)", color: "var(--chat-ai-text)", display: "flex", gap: "8px", alignItems: "center" }}>
            <div className="spinner" style={{ width: "16px", height: "16px", borderWidth: "1.5px" }}></div>
            <span style={{ fontSize: "14px" }}>Analyzing data...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div style={{ padding: "16px", borderTop: "1px solid var(--panel-border)" }}>
        <form onSubmit={handleSubmit} style={{ display: "flex", gap: "8px" }}>
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about your business data..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: "12px 16px",
              borderRadius: "8px",
              border: "1px solid var(--panel-border)",
              background: "#0f172a",
              color: "#f8fafc",
              fontSize: "14px",
              outline: "none",
              boxShadow: "inset 0 2px 4px rgba(0,0,0,0.1)"
            }}
            onFocus={(e) => e.target.style.borderColor = "var(--primary)"}
            onBlur={(e) => e.target.style.borderColor = "var(--panel-border)"}
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            style={{
              padding: "0 20px",
              borderRadius: "8px",
              background: inputMessage.trim() && !isLoading ? "var(--primary)" : "var(--panel-border)",
              color: "white",
              border: "none",
              cursor: inputMessage.trim() && !isLoading ? "pointer" : "not-allowed",
              fontWeight: "600",
              transition: "background 0.2s"
            }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
