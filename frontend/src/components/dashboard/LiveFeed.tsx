"use client";
import { useAgentStore } from "@/store/agentStore";
import { cn, formatConfidence, getSignalColor, timeAgo } from "@/lib/utils";
import { SignalPill, AssetBadge } from "@/components/shared";
import type { TradingSignal } from "@/types";
import { formatPrice } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import Link from "next/link";

// ─── ActiveSwarmFeed ─────────────────────────────────────────────────────────

export function ActiveSwarmFeed() {
  const { eventLog } = useAgentStore();

  return (
    <div className="glass-card flex flex-col" style={{ height: 320 }}>
      <div className="px-4 py-2.5 border-b border-border flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-cyber animate-pulse-slow" />
        <span className="text-xs font-medium text-muted-foreground tracking-wide uppercase">Live Event Feed</span>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-1.5 font-mono text-[11px]">
        {eventLog.length === 0 && (
          <p className="text-muted-foreground/40 text-center mt-8">Waiting for events…</p>
        )}
        {eventLog.map((e) => (
          <div key={e.id} className="flex items-start gap-2 animate-fade-in">
            <span className="text-muted-foreground/40 shrink-0 tabular-nums w-16">
              {new Date(e.timestamp).toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
            <span className="text-cyber/80 shrink-0 w-14">[{e.ticker}]</span>
            <span className="text-foreground/80 leading-relaxed">{e.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── SignalCard ───────────────────────────────────────────────────────────────

export function SignalCard({ signal, decisionId }: { signal: TradingSignal; decisionId?: string }) {
  const Icon = signal.signal === "BUY" ? TrendingUp : signal.signal === "SELL" ? TrendingDown : Minus;
  const iconColor = signal.signal === "BUY" ? "text-bull" : signal.signal === "SELL" ? "text-bear" : "text-hold";

  return (
    <Link
      href={decisionId ? `/journal/${decisionId}` : "#"}
      className="glass-card p-4 block hover:border-cyber/30 transition-colors animate-slide-in-up"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <AssetBadge ticker={signal.ticker} />
          <Icon className={cn("w-3.5 h-3.5", iconColor)} />
        </div>
        <SignalPill signal={signal.signal} size="sm" />
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
        <div>
          <span className="text-muted-foreground">Price</span>
          <p className="font-mono text-foreground">{formatPrice(signal.price_at_signal)}</p>
        </div>
        <div>
          <span className="text-muted-foreground">Net conf.</span>
          <p className={cn("font-mono", getSignalColor(signal.signal))}>
            {formatConfidence(signal.net_confidence)}
          </p>
        </div>
        <div>
          <span className="text-muted-foreground">Bull</span>
          <p className="font-mono text-bull">{formatConfidence(signal.bull_confidence)}</p>
        </div>
        <div>
          <span className="text-muted-foreground">Bear</span>
          <p className="font-mono text-bear">{formatConfidence(signal.bear_confidence)}</p>
        </div>
      </div>

      <p className="text-[10px] text-muted-foreground/60 mt-2 font-mono">
        {timeAgo(signal.created_at)}
      </p>
    </Link>
  );
}
