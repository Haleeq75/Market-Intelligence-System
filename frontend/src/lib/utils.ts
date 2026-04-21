import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow, format } from "date-fns";
import type { SignalType, ConfidenceLabel, DecisionStatus } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ─── Signal formatting ────────────────────────────────────────────────────────

export function getSignalColor(signal: SignalType | null | undefined) {
  switch (signal) {
    case "BUY":  return "text-bull";
    case "SELL": return "text-bear";
    case "HOLD": return "text-hold";
    default:     return "text-muted-foreground";
  }
}

export function getSignalBg(signal: SignalType | null | undefined) {
  switch (signal) {
    case "BUY":  return "bg-bull-bg border-bull/20 text-bull";
    case "SELL": return "bg-bear-bg border-bear/20 text-bear";
    case "HOLD": return "bg-hold-bg border-hold/20 text-hold";
    default:     return "bg-muted border-border text-muted-foreground";
  }
}

export function getSignalGlow(signal: SignalType | null | undefined) {
  switch (signal) {
    case "BUY":  return "shadow-glow-bull";
    case "SELL": return "shadow-glow-bear";
    default:     return "";
  }
}

// ─── Confidence formatting ────────────────────────────────────────────────────

export function formatConfidence(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

export function getLabelColor(label: ConfidenceLabel | null | undefined) {
  switch (label) {
    case "HIGH":   return "text-bull";
    case "MEDIUM": return "text-hold";
    case "LOW":    return "text-muted-foreground";
    default:       return "text-muted-foreground";
  }
}

// ─── Status formatting ────────────────────────────────────────────────────────

export function getStatusLabel(status: DecisionStatus): string {
  const map: Record<DecisionStatus, string> = {
    pending:          "Queued",
    running_ear:      "Ingesting Data",
    running_bull:     "Bull Analysing",
    running_bear:     "Bear Analysing",
    running_arbiter:  "Arbiter Deliberating",
    complete:         "Complete",
    error:            "Error",
  };
  return map[status] ?? status;
}

export function getStatusColor(status: DecisionStatus): string {
  if (status === "complete") return "text-bull";
  if (status === "error") return "text-bear";
  if (status === "pending") return "text-muted-foreground";
  return "text-cyber";
}

export function isRunning(status: DecisionStatus): boolean {
  return ["running_ear", "running_bull", "running_bear", "running_arbiter"].includes(status);
}

// ─── Date formatting ──────────────────────────────────────────────────────────

export function timeAgo(dateStr: string): string {
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
}

export function formatDate(dateStr: string): string {
  return format(new Date(dateStr), "MMM d, yyyy HH:mm");
}

// ─── Number formatting ────────────────────────────────────────────────────────

export function formatPrice(v: number | null | undefined, currency = "USD"): string {
  if (v == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(v);
}

export function formatPct(v: number | null | undefined): string {
  if (v == null) return "—";
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}
