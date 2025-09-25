import { useCallback, useEffect, useRef, useState } from "react";
import io from "socket.io-client";
import UsernameModal from "./UsernameModal";

const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5002";
const introMessage = {
  id: "system-intro",
  system: true,
  plaintext:
    "Welcome to Cryptiq. Messages are encapsulated with Kyber-768, signed with Dilithium-3, and verified in real time.",
};

export default function ChatBox() {
  const [auth, setAuth] = useState(null);
  const [messages, setMessages] = useState([introMessage]);
  const [input, setInput] = useState("");
  const [recipient, setRecipient] = useState("");
  const [status, setStatus] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const bottomRef = useRef(null);
  const messageIds = useRef(new Set());

  const appendMessage = useCallback(message => {
    setMessages(prev => {
      if (message.system) {
        return [...prev, message];
      }
      const exists = messageIds.current.has(message.id);
      if (exists) {
        return prev.map(item => (item.id === message.id ? { ...item, ...message } : item));
      }
      messageIds.current.add(message.id);
      return [...prev, message];
    });
  }, []);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? window.localStorage.getItem("cryptiq-session") : null;
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed?.token && parsed?.user) {
          setAuth(parsed);
        }
      } catch (err) {
        console.warn("Failed to restore session", err);
      }
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (auth) {
      window.localStorage.setItem("cryptiq-session", JSON.stringify(auth));
    } else {
      window.localStorage.removeItem("cryptiq-session");
    }
  }, [auth]);

  const fetchMessages = useCallback(async () => {
    if (!auth) return;
    setLoadingHistory(true);
    try {
      const response = await fetch(`${backendBaseUrl}/api/messages`, {
        headers: { Authorization: `Bearer ${auth.token}` },
      });
      if (!response.ok) {
        throw new Error("Failed to fetch messages");
      }
      const data = await response.json();
      data.messages.forEach(message => appendMessage(message));
    } catch (err) {
      setStatus(err.message);
    } finally {
      setLoadingHistory(false);
    }
  }, [auth, appendMessage]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!auth) return;
    let cancelled = false;
    fetchMessages();
    return () => {
      cancelled = true;
    };
  }, [auth, fetchMessages]);

  useEffect(() => {
    if (!auth) return;
    const socket = io(backendBaseUrl);
    socket.emit("join", { token: auth.token });
    socket.on("status", payload => setStatus(payload.message));
    socket.on("new_message", () => fetchMessages());
    socket.on("error", err => setStatus(err.error || "Socket error"));
    return () => {
      socket.disconnect();
    };
  }, [auth, fetchMessages]);

  async function sendMessage() {
    if (!input.trim() || !auth) return;
    setSending(true);
    try {
      const response = await fetch(`${backendBaseUrl}/api/messages/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${auth.token}`,
        },
        body: JSON.stringify({ recipient_username: recipient, plaintext: input }),
      });
      if (!response.ok) {
        throw new Error(payload.error || "Failed to dispatch message");
      }
      setInput("");
      fetchMessages();
    } catch (err) {
      setStatus(err.message);
    } finally {
      setSending(false);
    }
  }

  async function handleLogout() {
    if (!auth) return;
    try {
      await fetch(`${backendBaseUrl}/api/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${auth.token}` },
      });
    } catch (err) {
      console.warn("Logout warning", err);
    } finally {
      messageIds.current = new Set();
      setMessages([introMessage]);
      setAuth(null);
      setStatus("Disconnected");
    }
  }

  if (!auth) {
    return (
      <UsernameModal
        onAuthenticated={session => {
          setAuth(session);
          setStatus(`Authenticated as ${session.user.username}`);
        }}
      />
    );
  }

  return (
    <div className="w-full max-w-2xl bg-glass rounded-2xl shadow-[0_0_12px_2px_#08f7fe80] p-6 backdrop-blur-2xl border border-white/20 flex flex-col h-[70vh] relative">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-orbitron text-2xl text-neon">Quantum Chat</h2>
        <div className="flex items-center gap-3 text-whiteGlow text-sm">
          <span className="px-3 py-1 bg-white/10 rounded-full border border-white/10">
            {auth.user.username}
          </span>
          <button
            onClick={handleLogout}
            className="text-xs text-neon underline hover:text-whiteGlow"
          >
            Logout
          </button>
        </div>
      </div>
      {status && (
        <div className="mb-2 text-xs text-amber-200 bg-white/10 px-3 py-2 rounded-lg border border-white/10">
          {status}
        </div>
      )}
      {loadingHistory && (
        <div className="mb-2 text-xs text-whiteGlow/70">Synchronizing encrypted history…</div>
      )}
      <div className="flex-1 overflow-y-auto space-y-3 mb-4 bg-transparent pr-1">
        {messages.map(message =>
          message.system ? (
            <div key={message.id} className="text-whiteGlow text-center italic bg-transparent">
              {message.plaintext}
            </div>
          ) : (
            <div
              key={message.id}
              className={`text-whiteGlow bg-white/10 rounded-lg px-3 py-2 max-w-[85%] border ${
                message.sender === auth.user.username
                  ? "ml-auto border-neon"
                  : "border-white/10"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-bold text-neon">{message.sender}</span>
                <span className="text-xs text-whiteGlow/60">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className="mt-1 whitespace-pre-wrap break-words">{message.plaintext}</p>
              <div className="mt-2 text-xs flex items-center justify-between">
                <span className={message.signature_valid ? "text-emerald-300" : "text-rose-300"}>
                  {message.signature_valid ? "Dilithium signature verified" : "Signature invalid"}
                </span>
                <span className="text-whiteGlow/50">Kyber ciphertext length: {message.ciphertext.length}</span>
              </div>
              <details className="mt-2 text-xs text-whiteGlow/70">
                <summary className="cursor-pointer text-neon">Cryptographic payload</summary>
                <div className="mt-1 space-y-1">
                  <div>Kyber ciphertext: <span className="break-all">{message.kem_ciphertext}</span></div>
                  <div>Nonce: <span className="break-all">{message.nonce}</span></div>
                  <div>Tag: <span className="break-all">{message.tag}</span></div>
                  <div>Dilithium signature: <span className="break-all">{message.signature}</span></div>
                </div>
              </details>
            </div>
          )
        )}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 px-4 py-2 rounded-lg bg-white/20 text-whiteGlow border border-white/10 focus:outline-none focus:border-neon transition"
          value={recipient}
          onChange={e => setRecipient(e.target.value)}
          placeholder="Recipient username..."
        />
        <input
          className="flex-1 px-4 py-2 rounded-lg bg-white/20 text-whiteGlow border border-white/10 focus:outline-none focus:border-neon transition"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !sending && sendMessage()}
          placeholder="Compose an encrypted thought…"
        />
        <button
          className="bg-neon text-darkBg font-bold px-4 py-2 rounded-lg shadow-[0_0_8px_2px_#08f7fe60] hover:bg-whiteGlow transition disabled:opacity-60 disabled:cursor-not-allowed"
          onClick={sendMessage}
          disabled={sending}
        >
          {sending ? "Sending…" : "Send"}
        </button>
      </div>
      <footer className="text-center text-whiteGlow mt-4 text-xs">
        Post-quantum session secured with Kyber-768 & Dilithium-3
      </footer>
    </div>
  );
}
