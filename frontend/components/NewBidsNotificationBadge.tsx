"use client";

/**
 * STORY-445: NewBidsNotificationBadge
 *
 * Shows a red badge in the page header when new bids arrived since the user's
 * last search.  Polls /api/new-bids-count every 30 min via SWR.
 *
 * clearBadge() is called by buscar/page.tsx after a successful search.
 */

import useSWR, { mutate as globalMutate } from "swr";
import { useAuth } from "../app/components/AuthProvider";

const NEW_BIDS_KEY = "/api/new-bids-count";

async function fetcher(url: string, token: string): Promise<{ count: number }> {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return { count: 0 };
  return res.json();
}

/** Call this from page.tsx after a search completes to clear the badge. */
export async function clearNewBidsBadge(accessToken: string): Promise<void> {
  try {
    await fetch(NEW_BIDS_KEY, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch {
    // Best-effort; ignore errors
  }
  // Update SWR cache immediately so badge disappears without waiting for revalidation
  await globalMutate(NEW_BIDS_KEY, { count: 0 }, false);
}

export function NewBidsNotificationBadge() {
  const { session } = useAuth();
  const token = session?.access_token;

  const { data } = useSWR<{ count: number }>(
    token ? [NEW_BIDS_KEY, token] : null,
    ([url, t]: [string, string]) => fetcher(url, t),
    {
      refreshInterval: 30 * 60 * 1000, // 30 min
      revalidateOnFocus: true,
      dedupingInterval: 60_000,
    }
  );

  const count = data?.count ?? 0;

  if (!token || count === 0) return null;

  return (
    <div className="relative inline-flex items-center" data-testid="new-bids-badge">
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-500 text-white shadow-sm"
        title={`${count} ${count === 1 ? "novo edital" : "novos editais"} disponíveis`}
        aria-label={`${count} ${count === 1 ? "novo edital" : "novos editais"} disponíveis`}
      >
        <svg
          className="w-3 h-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        {count > 99 ? "99+" : count}
      </span>
    </div>
  );
}
