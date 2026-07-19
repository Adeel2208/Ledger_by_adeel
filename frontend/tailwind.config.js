/** @type {import('tailwindcss').Config}
 * Palette + type from the ui-ux-pro-max "Data-Dense Dashboard" design system
 * (design-system/the-vc-brain/MASTER.md): trustworthy blue + amber, light mode,
 * Fira Sans / Fira Code. WCAG AA contrast.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces (light)
        canvas: "#f8fafc",       // --color-background
        surface: "#ffffff",
        raised: "#eef2f8",       // --color-muted (inputs / raised)
        border: "#dbeafe",       // --color-border (soft blue)
        // Text
        ink: "#1e293b",          // readable slate for body
        heading: "#1e3a8a",      // --color-foreground (deep blue for headings)
        muted: "#5b6472",
        faint: "#94a3b8",
        // Brand (primary blue + amber accent)
        accent: "#1e40af",       // --color-primary
        "accent-soft": "#3b82f6", // --color-secondary
        cta: "#d97706",          // --color-accent (amber highlight)
        // The three independent axes — kept visually distinct so scores never blend
        founder: "#6366f1",      // indigo
        market: "#059669",       // emerald
        idea: "#d97706",         // amber
        // Confidence tiers
        verified: "#059669",
        corroborated: "#2563eb",
        claimed: "#d97706",
        scraped: "#64748b",
        // Status
        danger: "#dc2626",       // --color-destructive
        success: "#059669",
      },
      fontFamily: {
        sans: ['"Fira Sans"', "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
        mono: ['"Fira Code"', "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(30,58,138,0.05), 0 1px 3px rgba(30,58,138,0.08)",
        glow: "0 0 0 1px rgba(30,64,175,0.35), 0 8px 24px rgba(30,64,175,0.12)",
      },
      borderRadius: {
        xl: "0.875rem",
      },
      transitionDuration: {
        DEFAULT: "200ms", // skill checklist: hover transitions 150-300ms
      },
    },
  },
  plugins: [],
};
