import { getSignals } from "@/lib/api";
import { cn, formatDate, formatPrice, formatConfidence, getSignalBg, getSignalColor } from "@/lib/utils";
import { AssetBadge, SignalPill, ConfidenceBar } from "@/components/shared";
import { TrendingUp } from "lucide-react";
import Link from "next/link";
import type { TradingSignal } from "@/types";

export const dynamic = "force-dynamic";

export default async function SignalsPage() {
  let signals: TradingSignal[] = [];
  try {
    signals = await getSignals({ limit: 100 });
  } catch {}

  const buys  = signals.filter((s) => s.signal === "BUY").length;
  const sells = signals.filter((s) => s.signal === "SELL").length;
  const holds = signals.filter((s) => s.signal === "HOLD").length;
  const avgConf = signals.length
    ? signals.reduce((a, s) => a + Number(s.net_confidence), 0) / signals.length
    : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-semibold">Signal History</h1>
        <p className="text-sm text-muted-foreground mt-0.5">All BUY / HOLD / SELL signals emitted by the swarm</p>
      </div>

      {/* Summary bar */}
      <div className="glass-card px-6 py-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "BUY signals",  value: buys,                       color: "text-bull" },
          { label: "SELL signals", value: sells,                      color: "text-bear" },
          { label: "HOLD signals", value: holds,                      color: "text-hold" },
          { label: "Avg net conf", value: formatConfidence(avgConf),  color: "text-cyber" },
        ].map(({ label, value, color }) => (
          <div key={label} className="text-center">
            <p className={cn("text-2xl font-mono font-semibold tabular-nums", color)}>{value}</p>
            <p className="text-[11px] text-muted-foreground mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Table */}
      {signals.length === 0 ? (
        <div className="glass-card p-12 flex flex-col items-center justify-center text-center">
          <TrendingUp className="w-10 h-10 text-muted-foreground/20 mb-3" />
          <p className="text-sm text-muted-foreground">No signals yet</p>
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                {["Asset", "Signal", "Bull", "Bear", "Net Conf.", "Price", "Date"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {signals.map((s) => (
                <tr key={s.id} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-4 py-3">
                    <AssetBadge ticker={s.ticker} />
                  </td>
                  <td className="px-4 py-3">
                    <SignalPill signal={s.signal} size="sm" />
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-bull font-mono text-xs">
                      {formatConfidence(Number(s.bull_confidence))}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-bear font-mono text-xs">
                      {formatConfidence(Number(s.bear_confidence))}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn("font-mono text-xs font-semibold", getSignalColor(s.signal))}>
                      {formatConfidence(Number(s.net_confidence))}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs text-foreground/70">
                      {formatPrice(s.price_at_signal)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-muted-foreground font-mono">
                      {formatDate(s.created_at)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
