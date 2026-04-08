"use client";

import type { SearchError } from "../useSearch";
import { getUserFriendlyError, getMessageFromErrorCode, CLIENT_TIMEOUT_STATUS } from "../../../../lib/error-messages";
import { recoverPartialSearch } from "../../../../lib/searchPartialCache";
import type { BuscaResult } from "../../../types";

export interface SearchErrorMeta {
  errorCode: string | null;
  searchId: string;
  correlationId: string | null;
  requestId: string | null;
  httpStatus: number;
  rawMessage: string;
}

type ErrorWithMeta = Error & { _searchErrorMeta?: SearchErrorMeta };

export function attachErrorMeta(error: Error, meta: SearchErrorMeta): ErrorWithMeta {
  (error as ErrorWithMeta)._searchErrorMeta = meta;
  return error as ErrorWithMeta;
}

export function getErrorMeta(e: unknown): SearchErrorMeta | undefined {
  if (e !== null && typeof e === "object" && "_searchErrorMeta" in e) {
    return (e as ErrorWithMeta)._searchErrorMeta;
  }
  return undefined;
}

export function buildSearchError(e: unknown, searchId: string): SearchError {
  const rawMsg = e instanceof Error ? e.message : String(e);
  const errMeta = getErrorMeta(e);
  const errorCode = errMeta?.errorCode || null;
  const friendlyFromCode = getMessageFromErrorCode(errorCode);
  const friendlyMessage = friendlyFromCode || getUserFriendlyError(e);

  return {
    message: friendlyMessage,
    rawMessage: errMeta?.rawMessage || rawMsg,
    errorCode,
    searchId: errMeta?.searchId || searchId,
    correlationId: errMeta?.correlationId || null,
    requestId: errMeta?.requestId || null,
    httpStatus: errMeta?.httpStatus || null,
    timestamp: new Date().toISOString(),
  };
}

export function recoverPartialOnTimeout(
  searchId: string,
): BuscaResult | null {
  const partial = recoverPartialSearch(searchId);
  if (partial && partial.partialResult) {
    return partial.partialResult as BuscaResult;
  }
  // Check sessionStorage fallback
  try {
    const partialKey = `partial_search_${searchId}`;
    const partialRaw = sessionStorage.getItem(partialKey);
    if (partialRaw) {
      const partialData = JSON.parse(partialRaw) as { rawCount: number; timestamp: number };
      if (partialData.rawCount > 0 && Date.now() - partialData.timestamp < 300000) {
        sessionStorage.removeItem(partialKey);
      }
    }
  } catch { /* ignore */ }
  return null;
}

export function isTimeoutError(searchError: SearchError): boolean {
  return (
    searchError.httpStatus === CLIENT_TIMEOUT_STATUS ||
    searchError.httpStatus === 504 ||
    Boolean(searchError.rawMessage?.toLowerCase().includes("timeout")) ||
    Boolean(searchError.rawMessage?.toLowerCase().includes("demorou"))
  );
}
