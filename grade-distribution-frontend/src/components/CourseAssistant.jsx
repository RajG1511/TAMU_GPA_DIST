import React, { useState } from "react";

export default function CourseAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/rag/advise", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: input,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();
      const assistantMessage = {
        role: "assistant",
        content: data.advice,
        sources: data.sources,
      };

      setMessages([...updatedMessages, assistantMessage]);
    } catch (error) {
      console.error("Error:", error);
      const errorMessage = {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
      };
      setMessages([...updatedMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "70vh" }}>
      <div style={{ marginBottom: "1rem", textAlign: "center" }}>
        <h2>Course Assistant</h2>
        <p style={{ color: "#ccc", fontSize: "0.9rem" }}>
          Ask me about courses, compare professors, or get advice on class selection
        </p>
      </div>

      {/* Chat messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          border: "1px solid #444",
          borderRadius: "8px",
          padding: "1rem",
          marginBottom: "1rem",
          backgroundColor: "#222",
        }}
      >
        {messages.length === 0 ? (
          <div style={{ color: "#888", textAlign: "center", marginTop: "2rem" }}>
            <p>Start a conversation! Try asking:</p>
            <ul style={{ textAlign: "left", maxWidth: "400px", margin: "1rem auto" }}>
              <li>"Compare CSCE 121 and CSCE 221"</li>
              <li>"Which professor should I take for MATH 151?"</li>
              <li>"What are the easiest ENGR electives?"</li>
              <li>"Tell me about PHYS 206 difficulty"</li>
            </ul>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              style={{
                marginBottom: "1rem",
                padding: "0.8rem",
                borderRadius: "8px",
                backgroundColor: message.role === "user" ? "#333" : "#1a4d3a",
                maxWidth: "80%",
                alignSelf: message.role === "user" ? "flex-end" : "flex-start",
                marginLeft: message.role === "user" ? "auto" : "0",
              }}
            >
              <div style={{ fontWeight: "bold", marginBottom: "0.5rem" }}>
                {message.role === "user" ? "You" : "Assistant"}
              </div>
              <div style={{ whiteSpace: "pre-wrap" }}>{message.content}</div>
              {message.sources && message.sources.length > 0 && (
                <div style={{ marginTop: "0.8rem", fontSize: "0.8rem", color: "#aaa" }}>
                  <strong>Sources:</strong>
                  <ul style={{ margin: "0.5rem 0", paddingLeft: "1.5rem" }}>
                    {message.sources.slice(0, 3).map((source, idx) => (
                      <li key={idx}>
                        {source.metadata?.course_id && (
                          <span style={{ fontWeight: "bold", color: "#4a9eff" }}>
                            {source.metadata.course_id}
                          </span>
                        )}
                        {source.metadata?.instructor && (
                          <span> - Prof. {source.metadata.instructor}</span>
                        )}
                        {source.metadata?.term && (
                          <span> ({source.metadata.term})</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div
            style={{
              padding: "0.8rem",
              borderRadius: "8px",
              backgroundColor: "#1a4d3a",
              maxWidth: "80%",
            }}
          >
            <div style={{ fontWeight: "bold", marginBottom: "0.5rem" }}>Assistant</div>
            <div>Thinking...</div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <form onSubmit={handleSubmit} style={{ flex: 1, display: "flex", gap: "0.5rem" }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about courses, professors, or get study advice..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: "0.8rem",
              borderRadius: "4px",
              border: "1px solid #444",
              backgroundColor: "#333",
              color: "white",
              outline: "none",
            }}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            style={{
              padding: "0.8rem 1.5rem",
              borderRadius: "4px",
              border: "none",
              backgroundColor: isLoading || !input.trim() ? "#555" : "#4a9eff",
              color: "white",
              cursor: isLoading || !input.trim() ? "not-allowed" : "pointer",
            }}
          >
            Send
          </button>
        </form>
        <button
          onClick={clearChat}
          style={{
            padding: "0.8rem 1rem",
            borderRadius: "4px",
            border: "1px solid #666",
            backgroundColor: "transparent",
            color: "#ccc",
            cursor: "pointer",
          }}
        >
          Clear
        </button>
      </div>
    </div>
  );
}