
export default function Home() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-darkBg via-glass to-black">
      <div className="bg-glass rounded-2xl shadow-neon p-8 max-w-lg w-full text-center backdrop-blur-2xl border border-white/20">
        <h1 className="font-orbitron text-4xl text-whiteGlow mb-2 tracking-widest">
          Cryptiq
        </h1>
        <p className="text-whiteGlow/90 mb-6">Quantum-Safe Messenger</p>
        <a href="/chat" className="inline-block bg-neon hover:shadow-neon text-darkBg font-bold rounded-xl px-6 py-2 transition shadow-lg">Enter Chat</a>
      </div>
    </div>
  );
}
