"use client";
import { cn, getSignalBg, getStatusColor, getStatusLabel, isRunning } from "@/lib/utils";
import type { SignalType, DecisionStatus } from "@/types";
import { Loader2 } from "lucide-react";

// ─── SignalPill ───────────────────────────────────────────────────────────────
interface SignalPillProps {
  signal: SignalType | null | undefined;
  size?: "sm" | "md" | "lg";
}

export function SignalPill({ signal, size = "md" }: SignalPillProps) {
  if (!signal) return <span className="text-muted-foreground text-xs">—</span>;

  return (
    <span className={cn(
      "inline-flex items-center font-mono font-bold rounded border tracking-wider",
      getSignalBg(signal),
      size === "sm" && "px-1.5 py-0.5 text-[11px]",
      size === "md" && "px-2.5 py-1 text-xs",
      size === "lg" && "px-4 py-1.5 text-sm",
    )}>
      {signal}
    </span>
  );
}

// ─── StatusBadge ─────────────────────────────────────────────────────────────
interface StatusBadgeProps {
  status: DecisionStatus;
  showSpinner?: boolean;
}

export function StatusBadge({ status, showSpinner = true }: StatusBadgeProps) {
  const running = isRunning(status);
  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 text-xs",
      getStatusColor(status)
    )}>
      {running && showSpinner && <Loader2 className="w-3 h-3 animate-spin" />}
      {getStatusLabel(status)}
    </span>
  );
}

// ─── ConfidenceBar ────────────────────────────────────────────────────────────
interface ConfidenceBarProps {
  bull: number;
  bear: number;
  className?: string;
}

export function ConfidenceBar({ bull, bear, className }: ConfidenceBarProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center gap-2">
        <span className="text-[11px] text-muted-foreground w-8">Bull</span>
        <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
          <div
            className="h-full bg-bull/80 rounded-full transition-all duration-700"
            style={{ width: `${bull * 100}%` }}
          />
        </div>
        <span className="text-[11px] font-mono text-bull w-10 text-right">
          {(bull * 100).toFixed(0)}%
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[11px] text-muted-foreground w-8">Bear</span>
        <div className="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
          <div
            className="h-full bg-bear/80 rounded-full transition-all duration-700"
            style={{ width: `${bear * 100}%` }}
          />
        </div>
        <span className="text-[11px] font-mono text-bear w-10 text-right">
          {(bear * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
}

// ─── AssetBadge ───────────────────────────────────────────────────────────────
export function AssetBadge({ ticker }: { ticker: string }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-3 border border-border text-xs font-mono font-semibold text-foreground tracking-wide">
      {ticker}
    </span>
  );
}
