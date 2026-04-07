"use client";

/**
 * Zero-Churn P2 §8.2: Trial Extension Card.
 *
 * Shows trial users a checklist of actions they can complete to earn
 * extra trial days (up to 7 total). Only visible for free_trial plan users.
 */

import { useState } from "react";
import useSWR from "swr";
import { useAuth } from "../../app/components/AuthProvider";
import { usePlan } from "../../hooks/usePlan";

interface ExtensionItem {
  condition: string;
  label: string;
  days: number;
  claimed: boolean;
  eligible: boolean;
}

interface ExtensionsStatus {
  enabled: boolean;
  extensions: ExtensionItem[];
  total_extended: number;
  max_extension: number;
  remaining: number;
}

const CONDITION_ICONS: Record<string, string> = {
  profile_complete: "👤",
  feedback_given: "💬",
  referral_signup: "🤝",
};

const CONDITION_CTAS: Record<string, { text: string; href: string }> = {
  profile_complete: { text: "Completar perfil", href: "/conta" },
  feedback_given: { text: "Dar feedback", href: "/buscar" },
  referral_signup: { text: "Convidar colega", href: "/conta?tab=referral" },
};

const fetcher = async (url: string, token: string) => {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch");
  return res.json();
};

export function TrialExtensionCard() {
  const { session } = useAuth();
  const { planInfo } = usePlan();
  const [claiming, setClaiming] = useState<string | null>(null);

  const isTrial = planInfo?.plan_id === "free_trial";
  const token = session?.access_token;

  const { data, mutate } = useSWR<ExtensionsStatus>(
    isTrial && token ? ["/api/trial/extensions", token] : null,
    ([url, t]) => fetcher(url, t as string),
    { revalidateOnFocus: false }
  );

  if (!data?.enabled || !isTrial) return null;

  const handleClaim = async (condition: string) => {
    if (!token) return;
    setClaiming(condition);
    try {
      const res = await fetch("/api/trial/extend", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ condition }),
      });
      if (res.ok) {
        await mutate();
      }
    } finally {
      setClaiming(null);
    }
  };

  const progressPct = Math.min(
    100,
    data.max_extension > 0
      ? (data.total_extended / data.max_extension) * 100
      : 0
  );

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
      <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">
        Ganhe mais dias de trial
      </h3>
      <p className="text-xs text-blue-700 dark:text-blue-300 mb-3">
        Complete acoes para estender seu trial em ate {data.max_extension} dias
      </p>

      {/* Progress bar */}
      <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2 mb-1">
        <div
          className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-500"
          style={{ width: `${progressPct}%` }}
        />
      </div>
      <p className="text-xs text-blue-600 dark:text-blue-400 mb-3">
        {data.total_extended}/{data.max_extension} dias extras obtidos
      </p>

      {/* Extension items */}
      <div className="space-y-2">
        {data.extensions.map((ext) => (
          <div
            key={ext.condition}
            className={`flex items-center justify-between p-2 rounded ${
              ext.claimed
                ? "bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800"
                : "bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-base" aria-hidden="true">
                {CONDITION_ICONS[ext.condition] ?? "🎯"}
              </span>
              <div>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {ext.label}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                  +{ext.days} {ext.days === 1 ? "dia" : "dias"}
                </span>
              </div>
            </div>
            <div>
              {ext.claimed ? (
                <span className="text-xs text-green-600 dark:text-green-400 font-medium flex items-center gap-1">
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Concluido
                </span>
              ) : ext.eligible ? (
                <button
                  onClick={() => handleClaim(ext.condition)}
                  disabled={claiming === ext.condition}
                  className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {claiming === ext.condition ? "..." : "Resgatar"}
                </button>
              ) : (
                <a
                  href={CONDITION_CTAS[ext.condition]?.href ?? "#"}
                  className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                >
                  {CONDITION_CTAS[ext.condition]?.text ?? "Completar"}
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
