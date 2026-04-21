import { apiFetch } from "./client";
import type {
  AnalysisStartedResponse,
  AuthTokens,
  Asset,
  DecisionDetail,
  DecisionSummary,
  PaginatedResponse,
  TradingSignal,
  User,
} from "@/types";

// ─── Auth ─────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<AuthTokens> {
  const form = new URLSearchParams({ username: email, password });
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/auth/token`,
    { method: "POST", body: form, headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );
  if (!res.ok) throw new Error("Invalid credentials");
  return res.json();
}

export async function register(
  email: string,
  password: string,
  fullName?: string
): Promise<User> {
  return apiFetch<User>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  }, false);
}

export async function getMe(): Promise<User> {
  return apiFetch<User>("/api/v1/auth/me");
}

// ─── Analysis ─────────────────────────────────────────────────────────────────

export async function runAnalysis(ticker: string): Promise<AnalysisStartedResponse> {
  return apiFetch<AnalysisStartedResponse>("/api/v1/analysis/run", {
    method: "POST",
    body: JSON.stringify({ ticker }),
  });
}

export async function getAnalysisStatus(
  decisionId: string
): Promise<{ decision_id: string; status: string; ticker: string }> {
  return apiFetch(`/api/v1/analysis/status/${decisionId}`);
}

// ─── Journal ──────────────────────────────────────────────────────────────────

export async function getJournalEntries(params?: {
  ticker?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<DecisionSummary>> {
  const qs = new URLSearchParams();
  if (params?.ticker) qs.set("ticker", params.ticker);
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  return apiFetch(`/api/v1/journal?${qs}`);
}

export async function getDecisionDetail(id: string): Promise<DecisionDetail> {
  return apiFetch<DecisionDetail>(`/api/v1/journal/${id}`);
}

// ─── Signals ──────────────────────────────────────────────────────────────────

export async function getSignals(params?: {
  ticker?: string;
  limit?: number;
}): Promise<TradingSignal[]> {
  const qs = new URLSearchParams();
  if (params?.ticker) qs.set("ticker", params.ticker);
  if (params?.limit) qs.set("limit", String(params.limit));
  return apiFetch(`/api/v1/signals?${qs}`);
}

// ─── Assets ───────────────────────────────────────────────────────────────────

export async function getAssets(): Promise<Asset[]> {
  return apiFetch<Asset[]>("/api/v1/assets");
}

export async function addAsset(
  ticker: string,
  name?: string,
  assetClass = "equity"
): Promise<Asset> {
  return apiFetch<Asset>("/api/v1/assets", {
    method: "POST",
    body: JSON.stringify({ ticker, name, asset_class: assetClass }),
  });
}

export async function deleteAsset(id: string): Promise<void> {
  return apiFetch<void>(`/api/v1/assets/${id}`, { method: "DELETE" });
}
