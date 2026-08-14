import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Cinematic dark/blue fintech palette — consistent with the
        // visual direction used across the analyst dashboard.
        background: {
          DEFAULT: "#05070D",
          surface: "#0B0F1A",
          elevated: "#111827",
        },
        accent: {
          DEFAULT: "#3B82F6",
          soft: "#60A5FA",
          muted: "#1E3A8A",
        },
        risk: {
          low: "#22C55E",
          medium: "#EAB308",
          high: "#F97316",
          critical: "#EF4444",
        },
        border: {
          subtle: "#1F2937",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(59, 130, 246, 0.25)",
      },
    },
  },
  plugins: [],
} satisfies Config;
