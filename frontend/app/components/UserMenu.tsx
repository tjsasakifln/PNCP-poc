"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "./AuthProvider";
import Link from "next/link";

export function UserMenu() {
  const { user, session, loading, signOut, isAdmin } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  if (loading) return null;

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Link
          href="/login"
          className="px-4 py-2 text-sm text-[var(--ink)] border border-[var(--border)]
                     rounded-button hover:bg-[var(--surface-1)] transition-colors"
        >
          Entrar
        </Link>
        <Link
          href="/signup"
          className="px-4 py-2 text-sm bg-[var(--brand-navy)] text-white
                     rounded-button hover:bg-[var(--brand-blue)] transition-colors"
        >
          Criar conta
        </Link>
      </div>
    );
  }

  const initial = (user.email || "U")[0].toUpperCase();

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-9 h-9 rounded-full bg-[var(--brand-blue)] text-white
                   flex items-center justify-center text-sm font-semibold
                   hover:bg-[var(--brand-blue-hover)] transition-colors"
        title={user.email || ""}
      >
        {initial}
      </button>

      {open && (
        <div className="absolute right-0 top-11 w-56 bg-[var(--surface-0)] border border-[var(--border)]
                        rounded-card shadow-lg z-50 py-2">
          <div className="px-4 py-2 border-b border-[var(--border)]">
            <p className="text-sm font-medium text-[var(--ink)] truncate">{user.email}</p>
          </div>
          <Link href="/conta" onClick={() => setOpen(false)}
            className="block px-4 py-2 text-sm text-[var(--ink)] hover:bg-[var(--surface-1)]">
            Minha conta
          </Link>
          <Link href="/historico" onClick={() => setOpen(false)}
            className="block px-4 py-2 text-sm text-[var(--ink)] hover:bg-[var(--surface-1)]">
            Histórico
          </Link>
          <Link href="/planos" onClick={() => setOpen(false)}
            className="block px-4 py-2 text-sm text-[var(--ink)] hover:bg-[var(--surface-1)]">
            Planos
          </Link>
          {isAdmin && (
            <Link href="/admin" onClick={() => setOpen(false)}
              className="block px-4 py-2 text-sm text-[var(--ink)] hover:bg-[var(--surface-1)]">
              Admin
            </Link>
          )}
          <div className="border-t border-[var(--border)] mt-1 pt-1">
            <button
              onClick={() => { signOut(); setOpen(false); }}
              className="block w-full text-left px-4 py-2 text-sm text-[var(--error)] hover:bg-[var(--surface-1)]"
            >
              Sair
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
