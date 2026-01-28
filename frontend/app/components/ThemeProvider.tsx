"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

export type ThemeId = "light" | "paperwhite" | "sepia" | "dim" | "dark";

interface ThemeConfig {
  id: ThemeId;
  label: string;
  isDark: boolean;
  bg: string;
  fg: string;
  preview: string; // Color swatch for the toggle UI
}

export const THEMES: ThemeConfig[] = [
  { id: "light", label: "Light", isDark: false, bg: "#ffffff", fg: "#1a1a1a", preview: "#ffffff" },
  { id: "paperwhite", label: "Paperwhite", isDark: false, bg: "#F5F0E8", fg: "#1a1a1a", preview: "#F5F0E8" },
  { id: "sepia", label: "Sépia", isDark: false, bg: "#EDE0CC", fg: "#2c1810", preview: "#EDE0CC" },
  { id: "dim", label: "Dim", isDark: true, bg: "#2A2A2E", fg: "#e0e0e0", preview: "#2A2A2E" },
  { id: "dark", label: "Dark", isDark: true, bg: "#121212", fg: "#e0e0e0", preview: "#121212" },
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

  // Set CSS variables
  root.style.setProperty("--background", config.bg);
  root.style.setProperty("--foreground", config.fg);

  // Set semantic colors per theme
  if (config.isDark) {
    root.style.setProperty("--muted", "#a1a1aa");
    root.style.setProperty("--muted-foreground", "#d4d4d8");
    root.style.setProperty("--success", "#22c55e");
    root.style.setProperty("--success-bg", "#052e16");
    root.style.setProperty("--error", "#f87171");
    root.style.setProperty("--error-bg", "#450a0a");
    root.style.setProperty("--warning", "#facc15");
    root.style.setProperty("--warning-bg", "#422006");
    root.classList.add("dark");
  } else {
    root.style.setProperty("--muted", "#6b7280");
    root.style.setProperty("--muted-foreground", "#4b5563");
    root.style.setProperty("--success", "#16a34a");
    root.style.setProperty("--success-bg", config.id === "sepia" ? "#e8f5e9" : "#f0fdf4");
    root.style.setProperty("--error", "#dc2626");
    root.style.setProperty("--error-bg", config.id === "sepia" ? "#fce4ec" : "#fef2f2");
    root.style.setProperty("--warning", "#ca8a04");
    root.style.setProperty("--warning-bg", config.id === "sepia" ? "#fff8e1" : "#fefce8");
    root.classList.remove("dark");
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeId>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("bidiq-theme") as ThemeId | null;
    const initial = stored && THEMES.some(t => t.id === stored) ? stored : getSystemTheme();
    setThemeState(initial);
    applyTheme(initial);
    setMounted(true);
  }, []);

  const setTheme = useCallback((t: ThemeId) => {
    setThemeState(t);
    applyTheme(t);
    localStorage.setItem("bidiq-theme", t);
  }, []);

  const config = THEMES.find(t => t.id === theme) || THEMES[0];

  // Prevent flash of wrong theme
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, config }}>
      {children}
    </ThemeContext.Provider>
  );
}
