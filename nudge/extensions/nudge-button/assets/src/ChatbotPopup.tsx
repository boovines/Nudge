import React, { useEffect, useRef, useState } from "react";

type Role = "user" | "bot";
type Msg = { id: string; role: Role; text: string; ts: number };

const overlay: React.CSSProperties = {
  position: "fixed",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  background: "rgba(0,0,0,0.35)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 2147483646
};

const shell: React.CSSProperties = {
  width: "420px",
  maxWidth: "92%",
  background: "#fff",
  borderRadius: "10px",
  boxShadow: "0 10px 30px rgba(0,0,0,0.2)",
  overflow: "hidden",
  border: "1px solid #e5e7eb",
  display: "flex",
  flexDirection: "column"
};

const header: React.CSSProperties = {
  padding: "10px 12px",
  borderBottom: "1px solid #e5e7eb",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  fontWeight: 600
};

const closeBtn: React.CSSProperties = {
  appearance: "none",
  border: "none",
  background: "transparent",
  fontSize: "18px",
  cursor: "pointer",
  lineHeight: 1
};

const messagesWrap: React.CSSProperties = {
  padding: "12px",
  background: "#f9fafb",
  height: "300px",
  overflowY: "auto",
  display: "flex",
  flexDirection: "column",
  gap: "8px"
};

const rowBase: React.CSSProperties = {
  display: "flex",
  width: "100%"
};

const bubbleBase: React.CSSProperties = {
  padding: "8px 10px",
  borderRadius: "12px",
  maxWidth: "80%",
  fontSize: "14px",
  lineHeight: 1.35
};

const bubbleUser: React.CSSProperties = {
  ...bubbleBase,
  marginLeft: "auto",
  background: "#111827",
  color: "#fff"
};

const bubbleBot: React.CSSProperties = {
  ...bubbleBase,
  marginRight: "auto",
  background: "#ffffff",
  color: "#111827",
  border: "1px solid #e5e7eb"
};

const inputRow: React.CSSProperties = {
  padding: "10px",
  borderTop: "1px solid #e5e7eb",
  display: "flex",
  gap: "8px",
  alignItems: "center",
  flexWrap: "wrap"
};

const textInput: React.CSSProperties = {
  flex: 1,
  minWidth: 0,
  padding: "8px 10px",
  borderRadius: "8px",
  border: "1px solid #d1d5db",
  fontSize: "14px"
};

const primaryBtn: React.CSSProperties = {
  padding: "8px 12px",
  borderRadius: "8px",
  border: "1px solid #111827",
  background: "#111827",
  color: "#fff",
  fontSize: "14px",
  cursor: "pointer",
  whiteSpace: "nowrap",
  flexShrink: 0
};

const secondaryBtn: React.CSSProperties = {
  padding: "8px 12px",
  borderRadius: "8px",
  border: "1px solid #111827",
  background: "#fff",
  color: "#111827",
  fontSize: "14px",
  cursor: "pointer",
  whiteSpace: "nowrap",
  flexShrink: 0
};

function uuid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export default function ChatbotPopup({
  isOpen,
  onClose
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [value, setValue] = useState("");
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const timers = useRef<number[]>([]);

  // Load and persist messages in sessionStorage
  useEffect(() => {
    if (isOpen) {
      try {
        const raw = sessionStorage.getItem("nudge_msgs");
        if (raw) setMsgs(JSON.parse(raw));
        if (!raw) {
          const hello: Msg = {
            id: uuid(),
            role: "bot",
            text: "Hi. I can help with price and product questions.",
            ts: Date.now()
          };
          setMsgs([hello]);
        }
        setTimeout(() => inputRef.current?.focus(), 50);
      } catch {}
    }
    return () => {
      // clear any pending bot timers
      timers.current.forEach((t) => window.clearTimeout(t));
      timers.current = [];
    };
  }, [isOpen]);

  useEffect(() => {
    try {
      sessionStorage.setItem("nudge_msgs", JSON.stringify(msgs.slice(-50)));
    } catch {}
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [msgs]);

  const send = () => {
    const text = value.trim();
    if (!text) return;
    const userMsg: Msg = { id: uuid(), role: "user", text, ts: Date.now() };
    setMsgs((m) => [...m, userMsg]);
    setValue("");

    // Fake bot reply for MVP
    setTyping(true);
    const t = window.setTimeout(() => {
      const replyText =
        text.toLowerCase().includes("discount")
          ? "You can use code NUDGE10 for 10% off right now."
          : "Got it. I can also apply a 10% code if you need.";
      const botMsg: Msg = { id: uuid(), role: "bot", text: replyText, ts: Date.now() };
      setMsgs((m) => [...m, botMsg]);
      setTyping(false);
    }, 500);
    timers.current.push(t);
  };

  const apply = () => {
    const code = "NUDGE10"; // or read from DOM later if you prefer
    // remember so we can show live price preview on next page load
    try { localStorage.setItem("nudge_code", code); } catch {}
    const redirect = location.pathname + location.search;
    const url = `/discount/${encodeURIComponent(code)}?redirect=${encodeURIComponent(redirect)}`;
    location.assign(url);
  };
  
  

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  if (!isOpen) return null;

  return (
    <div style={overlay} onClick={onClose}>
      <div style={shell} onClick={(e) => e.stopPropagation()}>
        <div style={header}>
          <span>Nudge Chat</span>
          <button aria-label="Close chat" style={closeBtn} onClick={onClose}>
            ×
          </button>
        </div>

        <div ref={scrollRef} style={messagesWrap}>
          {msgs.map((m) => (
            <div key={m.id} style={rowBase}>
              <div style={m.role === "user" ? bubbleUser : bubbleBot}>{m.text}</div>
            </div>
          ))}
          {typing && (
            <div style={rowBase}>
              <div style={bubbleBot}>
                <span>Typing…</span>
              </div>
            </div>
          )}
        </div>

        <div style={inputRow}>
          <input
            ref={inputRef}
            style={textInput}
            type="text"
            placeholder="Type a message..."
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            aria-label="Message input"
          />
          <button style={primaryBtn} type="button" onClick={send}>
            Send
          </button>
          <button style={secondaryBtn} type="button" onClick={apply}>
            Apply 10% off
          </button>
        </div>
      </div>
    </div>
  );
}
