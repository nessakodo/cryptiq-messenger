import { useEffect, useState, useRef } from "react";
import io from "socket.io-client";
import UsernameModal from "./UsernameModal"; // Create this as shown earlier
let socket;

export default function ChatBox() {
  const [messages, setMessages] = useState([
    { message: "Welcome to Cryptiq! All messages are sent with quantum-safe encryption (Kyber/Dilithium). Open this chat in two tabs to test real-time messaging.", system: true }
  ]);
  const [input, setInput] = useState("");
  const [username, setUsername] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!username) return;
    socket = io(process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5002");
    socket.emit('join');
    socket.on("receive_message", (msg) => {
      setMessages((prev) => [...prev, msg]);
    });
    return () => socket && socket.disconnect();
  }, [username]);
  

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function sendMessage() {
    if (input.trim() && username) {
      socket.emit("send_message", { username, message: input });
      setInput("");
    }
  }

  if (!username) return <UsernameModal setUsername={setUsername} />;

  return (
    <div className="w-full max-w-2xl bg-glass rounded-2xl shadow-[0_0_12px_2px_#08f7fe80] p-6 backdrop-blur-2xl border border-white/20 flex flex-col h-[70vh] relative">
      {/* Security badge, lighter glow */}
      {/* <div className="absolute top-2 right-4 text-xs text-neon bg-white/5 px-3 py-1 rounded-full shadow-[0_0_8px_2px_#08f7fe60]">
        <span role="img" aria-label="lock">🔒</span> Quantum Safe: Kyber/Dilithium
      </div> */}
      <h2 className="font-orbitron text-2xl text-neon mb-3">Quantum Chat</h2>
      <div className="flex-1 overflow-y-auto space-y-2 mb-4 bg-transparent">
        {messages.map((msg, i) =>
          msg.system ? (
            <div
              key={i}
              className="text-whiteGlow text-center italic bg-transparent"
            >
              {msg.message}
            </div>
          ) : (
            <div
              key={i}
              className={
                msg.username === username
                  ? "text-whiteGlow bg-white/10 rounded-lg px-3 py-2 max-w-[80%] mx-auto border-l-4 border-neon"
                  : "text-whiteGlow bg-white/10 rounded-lg px-3 py-2 max-w-[80%] mx-auto"
              }
            >
              <span className="font-bold text-neon">{msg.username}: </span>
              {msg.message}
            </div>
          )
        )}
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
          className="bg-neon text-darkBg font-bold px-4 py-2 rounded-lg shadow-[0_0_8px_2px_#08f7fe60] hover:bg-whiteGlow transition"
          onClick={sendMessage}
        >
          Send
        </button>
      </div>
      <br></br>
      <footer className="text-center text-whiteGlow mt-4 text-xs">
        Powered by Kyber & Dilithium | Designed by Nessa Kodo
      </footer>
    </div>
  );
}
