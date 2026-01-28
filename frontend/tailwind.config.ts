import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class", // Controlled by ThemeProvider
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        muted: "var(--muted)",
        "muted-foreground": "var(--muted-foreground)",
        success: "var(--success)",
        "success-bg": "var(--success-bg)",
        error: "var(--error)",
        "error-bg": "var(--error-bg)",
        warning: "var(--warning)",
        "warning-bg": "var(--warning-bg)",
      },
      fontFamily: {
        body: ["var(--font-body)", "sans-serif"],
        display: ["var(--font-display)", "serif"],
        data: ["var(--font-data)", "monospace"],
      },
      fontSize: {
        base: ["1rem", { lineHeight: "1.6" }],
      },
    },
  },
  plugins: [],
};

export default config;
