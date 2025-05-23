import { useState } from "react";

export default function UsernameModal({ setUsername }) {
  const [input, setInput] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (input.trim()) setUsername(input.trim());
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-darkBg/95 z-50">
      <form
        onSubmit={handleSubmit}
        className="bg-glass p-12 rounded-2xl shadow-[0_0_18px_4px_#08f7fe40] border border-white/20 flex flex-col items-center max-w-md w-full"
      >
        <h2 className="font-orbitron text-3xl text-neon mb-6 tracking-wide drop-shadow-neon">
          Welcome to Cryptiq
        </h2>
        <p className="text-whiteGlow/90 mb-6 text-sm">
          Choose a unique username to enter the chat.
        </p>
        <input
          className="px-6 py-3 mb-6 rounded-xl bg-white/15 text-whiteGlow border border-white/10 focus:outline-none focus:border-neon text-center font-medium text-lg transition w-full"
          placeholder="Type your handle…"
          value={input}
          maxLength={20}
          onChange={e => setInput(e.target.value)}
          autoFocus
        />
        <button
          type="submit"
          className="w-full bg-neon text-darkBg font-bold px-8 py-3 rounded-xl shadow-[0_0_10px_2px_#08f7fe30] hover:bg-whiteGlow transition text-lg"
        >
          Enter Chat
        </button>
        <p className="text-whiteGlow/50 mt-4 text-xs">
          Your username will be visible to others in this session.
        </p>
      </form>
    </div>
  );
}
