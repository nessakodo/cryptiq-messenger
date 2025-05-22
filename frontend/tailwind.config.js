
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        orbitron: ['Orbitron', 'sans-serif'],
        inter: ['Inter', 'sans-serif'],
      },
      colors: {
        darkBg: "#141e30",
        glass: "rgba(36,59,85,0.72)",
        neon: "#08f7fe",
        whiteGlow: "#d8eeff",
      },
      boxShadow: {
        neon: "0 0 16px #08f7fe, 0 0 32px #08f7fe70",
      }
    },
  },
  plugins: [],
}
