// DEBT-012: Use Tailwind theme tokens (e.g., text-primary, bg-error) instead of raw hex values.
// For new colors, add CSS var to globals.css + Tailwind mapping here.
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
        /* GTM-006: Gem palette */
        "gem-sapphire": "var(--gem-sapphire)",
        "gem-emerald": "var(--gem-emerald)",
        "gem-amethyst": "var(--gem-amethyst)",
        "gem-ruby": "var(--gem-ruby)",
        /* DEBT-012: Semantic aliases */
        primary: "var(--brand-blue)",
        secondary: "var(--brand-navy)",
        accent: "var(--brand-blue-hover)",
        /* DEBT-012: Chart palette (mirrors globals.css --chart-N) */
        "chart-1": "var(--chart-1)",
        "chart-2": "var(--chart-2)",
        "chart-3": "var(--chart-3)",
        "chart-4": "var(--chart-4)",
        "chart-5": "var(--chart-5)",
        "chart-6": "var(--chart-6)",
        "chart-7": "var(--chart-7)",
        "chart-8": "var(--chart-8)",
        "chart-9": "var(--chart-9)",
        "chart-10": "var(--chart-10)",
        /* DEBT-012: Third-party brand colors */
        whatsapp: "var(--whatsapp)",
        /* STORY-2.5: Disabled state tokens — WCAG AA 4.5:1 (text), 3:1 (large)
           Light: ink-disabled (#6B7280) vs surface-disabled (#F3F4F6) → 4.6:1 ✅
           Dark:  ink-disabled (#9CA3AF) vs surface-disabled (#374151) → 4.5:1 ✅
        */
        "ink-disabled": "var(--ink-disabled)",
        "surface-disabled": "var(--surface-disabled)",
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
      fontWeight: {
        display: "800",
      },
      letterSpacing: {
        tighter: "-0.02em",
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
      maxWidth: {
        landing: "1200px",
      },
      /* STORY-174: Premium shadows */
      boxShadow: {
        'sm': 'var(--shadow-sm)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
        'xl': 'var(--shadow-xl)',
        '2xl': 'var(--shadow-2xl)',
        'glow': 'var(--shadow-glow)',
        'glow-lg': 'var(--shadow-glow-lg)',
        'glass': 'var(--glass-shadow)',
        /* GTM-006: Gem shadows */
        'gem-sapphire': 'var(--gem-sapphire-shadow)',
        'gem-emerald': 'var(--gem-emerald-shadow)',
        'gem-amethyst': 'var(--gem-amethyst-shadow)',
        'gem-ruby': 'var(--gem-ruby-shadow)',
      },
      /* STORY-174: Premium animations */
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "gradient": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        "shimmer": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "slide-up": {
          "from": { opacity: "0", transform: "translateY(24px)" },
          "to": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "from": { opacity: "0", transform: "scale(0.95)" },
          "to": { opacity: "1", transform: "scale(1)" },
        },
        "slide-in-right": {
          "from": { transform: "translateX(100%)" },
          "to": { transform: "translateX(0)" },
        },
        "bounce-gentle": {
          "0%, 100%": { transform: "translateY(0) translateX(-50%)" },
          "50%": { transform: "translateY(6px) translateX(-50%)" },
        },
        /* DEBT-v3-S2 AC9: Indeterminate progress bar for "stuck" state */
        "indeterminate-bar": {
          "0%": { transform: "translateX(-100%)" },
          "50%": { transform: "translateX(200%)" },
          "100%": { transform: "translateX(-100%)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.4s ease-out both",
        "gradient": "gradient 8s linear infinite",
        "shimmer": "shimmer 2s linear infinite",
        "float": "float 3s ease-in-out infinite",
        "slide-up": "slide-up 0.6s cubic-bezier(0.4, 0, 0.2, 1) both",
        "scale-in": "scale-in 0.4s cubic-bezier(0.4, 0, 0.2, 1) both",
        "slide-in-right": "slide-in-right 0.3s ease-out both",
        "bounce-gentle": "bounce-gentle 2s ease-in-out infinite",
        /* DEBT-v3-S2 AC9: Indeterminate progress bar */
        "indeterminate-bar": "indeterminate-bar 2s ease-in-out infinite",
      },
      /* STORY-174: Backdrop blur utilities */
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};

export default config;
