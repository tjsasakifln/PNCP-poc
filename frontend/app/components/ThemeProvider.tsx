"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

export type ThemeId = "light" | "paperwhite" | "sepia" | "dim" | "dark";

interface ThemeConfig {
  id: ThemeId;
  label: string;
  isDark: boolean;
  canvas: string;
  ink: string;
  preview: string;
}

export const THEMES: ThemeConfig[] = [
  { id: "light", label: "Light", isDark: false, canvas: "#ffffff", ink: "#1e2d3b", preview: "#ffffff" },
  { id: "paperwhite", label: "Paperwhite", isDark: false, canvas: "#F5F0E8", ink: "#1e2d3b", preview: "#F5F0E8" },
  { id: "sepia", label: "Sépia", isDark: false, canvas: "#EDE0CC", ink: "#2c1810", preview: "#EDE0CC" },
  { id: "dim", label: "Dim", isDark: true, canvas: "#2A2A2E", ink: "#e0e0e0", preview: "#2A2A2E" },
  { id: "dark", label: "Dark", isDark: true, canvas: "#121212", ink: "#e0e0e0", preview: "#121212" },
];

interface ThemeContextType {
  theme: ThemeId;
  setTheme: (t: ThemeId) => void;
  config: ThemeConfig;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "light",
  setTheme: () => {},
  config: THEMES[0],
});

export function useTheme() {
  return useContext(ThemeContext);
}

function getSystemTheme(): ThemeId {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(themeId: ThemeId) {
  const config = THEMES.find(t => t.id === themeId) || THEMES[0];
  const root = document.documentElement;

  root.style.setProperty("--canvas", config.canvas);
  root.style.setProperty("--ink", config.ink);

  if (config.isDark) {
    root.style.setProperty("--ink-secondary", "#a8b4c0");
    root.style.setProperty("--ink-muted", "#6b7a8a");
    root.style.setProperty("--ink-faint", "#3a4555");
    root.style.setProperty("--brand-blue-subtle", "rgba(17, 109, 255, 0.12)");
    root.style.setProperty("--surface-0", config.canvas);
    root.style.setProperty("--surface-1", "#1a1d22");
    root.style.setProperty("--surface-2", "#242830");
    root.style.setProperty("--surface-elevated", "#1e2128");
    root.style.setProperty("--success", "#22c55e");
    root.style.setProperty("--success-subtle", "#052e16");
    root.style.setProperty("--error", "#f87171");
    root.style.setProperty("--error-subtle", "#450a0a");
    root.style.setProperty("--warning", "#facc15");
    root.style.setProperty("--warning-subtle", "#422006");
    root.style.setProperty("--border", "rgba(255, 255, 255, 0.08)");
    root.style.setProperty("--border-strong", "rgba(255, 255, 255, 0.15)");
    root.style.setProperty("--ring", "#3b8bff");
    root.classList.add("dark");
  } else {
    root.style.setProperty("--ink-secondary", "#3d5975");
    root.style.setProperty("--ink-muted", "#808f9f");
    root.style.setProperty("--ink-faint", "#c0d2e5");
    root.style.setProperty("--brand-blue-subtle", config.id === "sepia" ? "#e8e0d4" : "#e8f0ff");
    root.style.setProperty("--surface-0", config.canvas);
    root.style.setProperty("--surface-1", config.id === "sepia" ? "#e8dcc8" : config.id === "paperwhite" ? "#efe9e0" : "#f7f8fa");
    root.style.setProperty("--surface-2", config.id === "sepia" ? "#e0d4be" : config.id === "paperwhite" ? "#e8e2d8" : "#f0f2f5");
    root.style.setProperty("--surface-elevated", config.canvas);
    root.style.setProperty("--success", "#16a34a");
    root.style.setProperty("--success-subtle", config.id === "sepia" ? "#e8f5e9" : "#f0fdf4");
    root.style.setProperty("--error", "#dc2626");
    root.style.setProperty("--error-subtle", config.id === "sepia" ? "#fce4ec" : "#fef2f2");
    root.style.setProperty("--warning", "#ca8a04");
    root.style.setProperty("--warning-subtle", config.id === "sepia" ? "#fff8e1" : "#fefce8");
    root.style.setProperty("--border", "rgba(0, 0, 0, 0.08)");
    root.style.setProperty("--border-strong", "rgba(0, 0, 0, 0.15)");
    root.style.setProperty("--ring", "#116dff");
    root.classList.remove("dark");
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeId>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("descomplicita-theme") as ThemeId | null;
    const initial = stored && THEMES.some(t => t.id === stored) ? stored : "light";
    setThemeState(initial);
    applyTheme(initial);
    setMounted(true);
  }, []);

  const setTheme = useCallback((t: ThemeId) => {
    setThemeState(t);
    applyTheme(t);
    localStorage.setItem("descomplicita-theme", t);
  }, []);

  const config = THEMES.find(t => t.id === theme) || THEMES[0];

  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, config }}>
      {children}
    </ThemeContext.Provider>
  );
}
