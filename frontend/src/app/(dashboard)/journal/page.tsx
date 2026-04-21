import Link from "next/link";
import { getJournalEntries } from "@/lib/api";
import { cn, formatDate, formatConfidence, getSignalBg, getStatusColor, getStatusLabel, timeAgo } from "@/lib/utils";
import { SignalPill, AssetBadge, ConfidenceBar, StatusBadge } from "@/components/shared";
import { BookOpen, ChevronRight, Clock } from "lucide-react";
import type { DecisionSummary } from "@/types";

export const dynamic = "force-dynamic";

export default async function JournalPage({
  searchParams,
}: {
  searchParams: { ticker?: string; page?: string };
}) {
  const page = Number(searchParams?.page ?? 1);
  const ticker = searchParams?.ticker;

  let result = { items: [] as DecisionSummary[], total: 0, pages: 1 };
  try {
    result = await getJournalEntries({ ticker, page, page_size: 15 });
  } catch {}

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Decision Journal</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Full audit trail of every agent reasoning chain
          </p>
        </div>
        <div className="text-xs text-muted-foreground font-mono bg-surface-2 border border-border rounded px-3 py-1.5">
          {result.total} decisions
        </div>
      </div>

      {/* Timeline */}
      {result.items.length === 0 ? (
        <EmptyJournal />
      ) : (
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-[19px] top-2 bottom-2 w-px bg-border" />

          <div className="space-y-3">
            {result.items.map((decision) => (
              <JournalRow key={decision.id} decision={decision} />
            ))}
          </div>
        </div>
      )}

      {/* Pagination */}
      {result.pages > 1 && (
        <div className="flex items-center gap-2 justify-center pt-2">
          {Array.from({ length: result.pages }, (_, i) => i + 1).map((p) => (
            <Link
              key={p}
              href={`/journal?page=${p}${ticker ? `&ticker=${ticker}` : ""}`}
              className={cn(
                "w-8 h-8 flex items-center justify-center rounded text-xs font-mono transition-colors",
                p === page
                  ? "bg-cyber/20 border border-cyber/40 text-cyber"
                  : "text-muted-foreground hover:bg-surface-2"
              )}
            >
              {p}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function JournalRow({ decision }: { decision: DecisionSummary }) {
  const isComplete = decision.status === "complete";
  const isError = decision.status === "error";

  return (
    <Link
      href={`/journal/${decision.id}`}
      className="group flex items-start gap-4 relative"
    >
      {/* Timeline dot */}
      <div className={cn(
        "relative z-10 w-10 h-10 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors",
        isComplete && decision.signal === "BUY"  && "bg-bull-bg border-bull/40 group-hover:border-bull",
        isComplete && decision.signal === "SELL" && "bg-bear-bg border-bear/40 group-hover:border-bear",
        isComplete && decision.signal === "HOLD" && "bg-hold-bg border-hold/40 group-hover:border-hold",
        isError  && "bg-surface-2 border-bear/30",
        !isComplete && !isError && "bg-surface-2 border-border",
      )}>
        {isComplete && decision.signal ? (
          <span className={cn(
            "text-[9px] font-mono font-black",
            getSignalBg(decision.signal).split(" ")[0],  // just the text color class
          )}>
            {decision.signal}
          </span>
        ) : (
          <Clock className="w-3.5 h-3.5 text-muted-foreground" />
        )}
      </div>

      {/* Card */}
      <div className={cn(
        "flex-1 glass-card p-4 transition-all",
        "group-hover:border-cyber/30 group-hover:bg-surface-2/40",
      )}>
        <div className="flex items-start justify-between gap-3">
          {/* Left */}
          <div className="flex items-center gap-2.5 flex-wrap">
            <AssetBadge ticker={decision.ticker} />
            {isComplete
              ? <SignalPill signal={decision.signal} size="sm" />
              : <StatusBadge status={decision.status} />
            }
            {decision.confidence_label && (
              <span className={cn(
                "text-[10px] font-mono px-1.5 py-0.5 rounded border",
                decision.confidence_label === "HIGH"   && "text-bull/80 border-bull/20 bg-bull-bg",
                decision.confidence_label === "MEDIUM" && "text-hold/80 border-hold/20 bg-hold-bg",
                decision.confidence_label === "LOW"    && "text-muted-foreground border-border bg-surface-3",
              )}>
                {decision.confidence_label}
              </span>
            )}
          </div>

          {/* Right */}
          <div className="flex items-center gap-3 shrink-0">
            <span className="text-[11px] text-muted-foreground font-mono">
              {formatDate(decision.created_at)}
            </span>
            <ChevronRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-cyber transition-colors" />
          </div>
        </div>

        {/* Confidence bars (when complete) */}
        {isComplete && decision.bull_confidence != null && decision.bear_confidence != null && (
          <div className="mt-3 pt-3 border-t border-border">
            <ConfidenceBar
              bull={Number(decision.bull_confidence)}
              bear={Number(decision.bear_confidence)}
            />
          </div>
        )}

        {isError && (
          <p className="text-xs text-bear/70 mt-2 font-mono">Analysis failed — click to view details</p>
        )}
      </div>
    </Link>
  );
}

function EmptyJournal() {
  return (
    <div className="glass-card p-12 flex flex-col items-center justify-center text-center">
      <BookOpen className="w-10 h-10 text-muted-foreground/20 mb-3" />
      <p className="text-sm font-medium text-muted-foreground">The journal is empty</p>
      <p className="text-xs text-muted-foreground/60 mt-1 max-w-xs">
        Run an analysis from the Control Tower. Each decision will appear here with the full Bull vs Bear debate.
      </p>
    </div>
  );
}
