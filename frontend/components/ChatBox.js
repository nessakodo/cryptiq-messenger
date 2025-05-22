
import { useEffect, useState, useRef } from "react";
import io from "socket.io-client";
let socket;

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    socket = io(process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5002");
    socket.on("receive_message", (msg) => {
      setMessages((prev) => [...prev, msg]);
    });
    return () => socket.disconnect();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function sendMessage() {
    if (input.trim()) {
      socket.emit("send_message", { message: input });
      setInput("");
    }
  }

  return (
    <div className="w-full max-w-2xl bg-glass rounded-2xl shadow-neon p-6 backdrop-blur-2xl border border-white/20 flex flex-col h-[70vh]">
      <h2 className="font-orbitron text-2xl text-neon mb-3">Quantum Chat</h2>
      <div className="flex-1 overflow-y-auto space-y-2 mb-4 bg-transparent">
        {messages.map((msg, i) => (
          <div key={i} className="text-whiteGlow bg-white/10 rounded-lg px-3 py-2 max-w-[80%] mx-auto">
            {msg.message}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 px-4 py-2 rounded-lg bg-white/20 text-whiteGlow border border-white/10 focus:outline-none focus:border-neon transition"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && sendMessage()}
          placeholder="Type your quantum message…"
        />
        <button
          className="bg-neon text-darkBg font-bold px-4 py-2 rounded-lg shadow-neon hover:bg-whiteGlow transition"
          onClick={sendMessage}
        >
          Send
        </button>
      </div>
    </div>
  );
}
