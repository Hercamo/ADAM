import type { Config } from "tailwindcss";

// Tailwind configuration for the BOSS Console.
// BOSS uses the ADAM palette: dim navy for background, soap-green to
// ohshat-red for the escalation ladder. Dimensions share the canonical
// colour tokens from the ADAM book so the console is visually
// consistent with the reference diagrams.

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        adam: {
          navy: "#0b1220",
          charcoal: "#111827",
          ink: "#020617",
          accent: "#60a5fa",
          mist: "#94a3b8",
        },
        tier: {
          soap: "#22c55e",
          moderate: "#eab308",
          elevated: "#f97316",
          high: "#ef4444",
          ohshat: "#7f1d1d",
        },
        dim: {
          security: "#2563eb",
          sovereignty: "#0ea5e9",
          financial: "#16a34a",
          regulatory: "#a855f7",
          reputational: "#f59e0b",
          rights: "#14b8a6",
          doctrinal: "#ec4899",
        },
      },
      fontFamily: {
        display: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
      boxShadow: {
        card: "0 1px 2px rgba(2, 6, 23, 0.25), 0 8px 24px rgba(2, 6, 23, 0.2)",
      },
    },
  },
  plugins: [],
};

export default config;
