import { useState } from "react";
import { askClaimAssistant } from "../services/api";
import "../styles/components/Chatbot.css";

export default function Chatbot() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage(event) {
    event.preventDefault();

    const value = question.trim();
    if (!value || loading) return;

    setMessages((old) => [...old, { role: "user", text: value }]);
    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const result = await askClaimAssistant(value);

      const answer =
        result?.answer ??
        result?.response ??
        result?.message ??
        result?.result;

      if (typeof answer !== "string") {
        throw new Error(
          "The API responded, but its answer field is not recognised. Check the /api/rag/chat response schema."
        );
      }

      setMessages((old) => [
        ...old,
        { role: "assistant", text: answer }
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="chat-panel">
      <div className="chat-heading">
        <div>
          <span className="eyebrow">RAG-POWERED ASSISTANT</span>
          <h2>Ask Claimora AI</h2>
          <p>Ask about insurance documents, claim steps and requirements.</p>
        </div>
        <span className="ai-orb">AI</span>
      </div>

      <div className="chat-messages" aria-live="polite">
        {messages.length === 0 && (
          <div className="chat-empty">
            <span className="chat-symbol">✦</span>
            <h3>How can I help?</h3>
            <p>Your question will be sent to the connected backend.</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            className={`chat-message ${message.role}`}
            key={`${index}-${message.role}`}
          >
            <strong>
              {message.role === "user" ? "You" : "Claimora AI"}
            </strong>
            <p>{message.text}</p>
          </div>
        ))}

        {loading && <p className="loading-text">Waiting for AI response…</p>}
      </div>

      {error && <div className="error-message">{error}</div>}

      <form className="chat-form" onSubmit={sendMessage}>
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask your insurance question..."
          aria-label="Insurance question"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? "Sending..." : "Send ↗"}
        </button>
      </form>
    </section>
  );
}

