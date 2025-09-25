import { useState } from "react";

const backendBaseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5002";

export default function UsernameModal({ onAuthenticated }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("login");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Username and password are required");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      const endpoint = mode === "register" ? "/api/auth/register" : "/api/auth/login";
      const response = await fetch(`${backendBaseUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Authentication failed");
      }
      onAuthenticated({
        token: payload.token,
        user: payload.user,
        keys: payload.keys,
      });
      setUsername("");
      setPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  function toggleMode() {
    setMode(prev => (prev === "login" ? "register" : "login"));
    setError("");
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-darkBg/95 z-50">
      <form
        onSubmit={handleSubmit}
        className="bg-glass p-12 rounded-2xl shadow-[0_0_18px_4px_#08f7fe40] border border-white/20 flex flex-col items-center max-w-md w-full"
      >
        <h2 className="font-orbitron text-3xl text-neon mb-6 tracking-wide drop-shadow-neon">
          {mode === "login" ? "Rejoin Cryptiq" : "Create Cryptiq Identity"}
        </h2>
        <p className="text-whiteGlow/90 mb-6 text-sm text-center">
          {mode === "login"
            ? "Enter your credentials to unlock your post-quantum keys."
            : "Register to mint Kyber + Dilithium keys protected by your password."}
        </p>
        <input
          className="px-6 py-3 mb-4 rounded-xl bg-white/15 text-whiteGlow border border-white/10 focus:outline-none focus:border-neon text-center font-medium text-lg transition w-full"
          placeholder="Quantum handle"
          value={username}
          maxLength={32}
          onChange={e => setUsername(e.target.value)}
          autoFocus
        />
        <input
          className="px-6 py-3 mb-2 rounded-xl bg-white/15 text-whiteGlow border border-white/10 focus:outline-none focus:border-neon text-center font-medium text-lg transition w-full"
          placeholder="Secret passphrase"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
        {error && <p className="text-rose-300 text-sm mb-4">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-neon text-darkBg font-bold px-8 py-3 rounded-xl shadow-[0_0_10px_2px_#08f7fe30] hover:bg-whiteGlow transition text-lg disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {submitting ? "Securing…" : mode === "login" ? "Unlock" : "Register"}
        </button>
        <button
          type="button"
          onClick={toggleMode}
          className="text-neon underline mt-4 text-sm hover:text-whiteGlow"
        >
          {mode === "login" ? "Need an account? Register" : "Already trusted? Sign in"}
        </button>
        <p className="text-whiteGlow/50 mt-4 text-xs text-center">
          Private keys are encrypted with your password and never shared with other users.
        </p>
      </form>
    </div>
  );
}
