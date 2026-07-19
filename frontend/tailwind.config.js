/** @type {import('tailwindcss').Config}
 * Premium light theme — AI-violet + cyan, glassmorphism, depth.
 * Direction from ui-ux-pro-max ("Modern Dark / AI purple + cyan"), rendered light.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces
        canvas: "#f5f5fb",       // soft cool-tinted page
        surface: "#ffffff",
        raised: "#f3f2fb",
        border: "#e9e8f4",
        // Text
        heading: "#1e1b4b",      // deep indigo
        ink: "#2c2a44",          // body
        muted: "#6b6a86",
        faint: "#a3a1b8",
        // Brand — violet→indigo gradient anchors
        brand1: "#6366f1",       // indigo
        brand2: "#8b5cf6",       // violet
        brand3: "#a855f7",       // purple
        accent: "#7c3aed",       // primary violet
        "accent-soft": "#8b5cf6",
        cyan: "#0891b2",         // interactive accent
        // Three independent axes (vivid, distinct)
        founder: "#6366f1",
        market: "#10b981",
        idea: "#f59e0b",
        // Confidence tiers
        verified: "#10b981",
        corroborated: "#3b82f6",
        claimed: "#f59e0b",
        scraped: "#94a3b8",
        cta: "#f59e0b",
        // Status
        danger: "#ef4444",
        success: "#10b981",
      },
      fontFamily: {
        display: ['"Space Grotesk"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['Inter', "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(30,27,75,0.04), 0 4px 16px rgba(30,27,75,0.06)",
        lift: "0 8px 30px rgba(99,102,241,0.14), 0 2px 8px rgba(30,27,75,0.06)",
        glow: "0 0 0 1px rgba(124,58,237,0.18), 0 10px 40px rgba(124,58,237,0.20)",
        ring: "0 6px 20px rgba(124,58,237,0.30)",
      },
      backgroundImage: {
        brand: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)",
        "brand-soft": "linear-gradient(135deg, rgba(99,102,241,0.12), rgba(168,85,247,0.12))",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s cubic-bezier(0.16,1,0.3,1) both",
      },
    },
  },
  plugins: [],
};
