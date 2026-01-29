import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        ink: "var(--ink)",
        "ink-secondary": "var(--ink-secondary)",
        "ink-muted": "var(--ink-muted)",
        "ink-faint": "var(--ink-faint)",
        "brand-navy": "var(--brand-navy)",
        "brand-blue": "var(--brand-blue)",
        "brand-blue-hover": "var(--brand-blue-hover)",
        "brand-blue-subtle": "var(--brand-blue-subtle)",
        "surface-0": "var(--surface-0)",
        "surface-1": "var(--surface-1)",
        "surface-2": "var(--surface-2)",
        "surface-elevated": "var(--surface-elevated)",
        success: "var(--success)",
        "success-subtle": "var(--success-subtle)",
        error: "var(--error)",
        "error-subtle": "var(--error-subtle)",
        warning: "var(--warning)",
        "warning-subtle": "var(--warning-subtle)",
      },
      borderColor: {
        DEFAULT: "var(--border)",
        strong: "var(--border-strong)",
        accent: "var(--border-accent)",
      },
      fontFamily: {
        body: ["var(--font-body)", "sans-serif"],
        display: ["var(--font-display)", "sans-serif"],
        data: ["var(--font-data)", "monospace"],
      },
      fontSize: {
        base: ["1rem", { lineHeight: "1.6" }],
      },
      borderRadius: {
        input: "4px",
        button: "6px",
        card: "8px",
        modal: "12px",
      },
      spacing: {
        // Enforce 4px base: 1=4px, 2=8px, 3=12px, 4=16px, 6=24px, 8=32px, 16=64px
      },
    },
  },
  plugins: [],
};

export default config;
