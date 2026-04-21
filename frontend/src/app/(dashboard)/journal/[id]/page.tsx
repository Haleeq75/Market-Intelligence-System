import { notFound } from "next/navigation";
import { getDecisionDetail } from "@/lib/api";
import {
  cn, formatDate, formatPrice, formatConfidence,
  getSignalBg, getSignalColor, getLabelColor
} from "@/lib/utils";
import { SignalPill, AssetBadge, ConfidenceBar } from "@/components/shared";
import {
  TrendingUp, TrendingDown, Scale, Database,
  Newspaper, ArrowLeft, ExternalLink,
  CheckCircle2, AlertTriangle
} from "lucide-react";
import Link from "next/link";
import type { DecisionDetail, SourceCitation } from "@/types";

export const dynamic = "force-dynamic";

export default async function DecisionPage({ params }: { params: { id: string } }) {
  let decision: DecisionDetail;
  try {
    decision = await getDecisionDetail(params.id);
  } catch {
    notFound();
  }

  const isComplete = decision.status === "complete";
  const mc = decision.market_context as Record<string, unknown>;

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      {/* Back */}
      <Link
        href="/journal"
        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Decision Journal
      </Link>

      {/* Header card */}
      <div className="glass-card p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3 flex-wrap">
            <AssetBadge ticker={decision.ticker} />
            {isComplete && <SignalPill signal={decision.signal} size="lg" />}
            {decision.confidence_label && (
              <span className={cn(
                "text-xs font-mono px-2 py-0.5 rounded border",
                getLabelColor(decision.confidence_label as any),
                "border-current/20 bg-current/5"
              )}>
                {decision.confidence_label} confidence
              </span>
            )}
          </div>
          <div className="text-right shrink-0">
            <p className="text-xs text-muted-foreground">{formatDate(decision.created_at)}</p>
            {decision.completed_at && (
              <p className="text-[10px] text-muted-foreground/50 mt-0.5">
                Completed {formatDate(decision.completed_at)}
              </p>
            )}
          </div>
        </div>

        {/* Market context strip */}
        {isComplete && (
          <div className="mt-5 pt-5 border-t border-border grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Metric label="Price at Signal" value={formatPrice(decision.price_at_signal)} />
            <Metric
              label="Current Price"
              value={mc.price ? formatPrice(mc.price as number) : "—"}
            />
            <Metric
              label="1-Day Change"
              value={mc.price_change_1d != null ? `${(mc.price_change_1d as number) >= 0 ? "+" : ""}${(mc.price_change_1d as number).toFixed(2)}%` : "—"}
              valueClass={mc.price_change_1d != null ? ((mc.price_change_1d as number) >= 0 ? "text-bull" : "text-bear") : ""}
            />
            <Metric label="P/E Ratio" value={mc.pe_ratio ? String(mc.pe_ratio) : "—"} />
          </div>
        )}

        {/* Confidence bars */}
        {isComplete && decision.bull_confidence != null && (
          <div className="mt-5 pt-5 border-t border-border">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground">Confidence breakdown</span>
              <span className="text-xs font-mono text-muted-foreground">
                Net: <span className={getSignalColor(decision.signal)}>{formatConfidence(decision.net_confidence)}</span>
              </span>
            </div>
            <ConfidenceBar
              bull={Number(decision.bull_confidence)}
              bear={Number(decision.bear_confidence)}
            />
          </div>
        )}
      </div>

      {/* Arbiter Verdict */}
      {isComplete && decision.arbiter_reasoning && (
        <ArbiterVerdictBlock
          signal={decision.signal!}
          reasoning={decision.arbiter_reasoning}
        />
      )}

      {/* Bull vs Bear debate */}
      {(decision.bull_thesis || decision.bear_thesis) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ThesisBlock
            side="bull"
            thesis={decision.bull_thesis}
            confidence={Number(decision.bull_confidence)}
            sources={decision.bull_sources}
          />
          <ThesisBlock
            side="bear"
            thesis={decision.bear_thesis}
            confidence={Number(decision.bear_confidence)}
            sources={decision.bear_sources}
          />
        </div>
      )}

      {/* Error state */}
      {decision.status === "error" && decision.error_message && (
        <div className="glass-card p-5 border-bear/30">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-bear" />
            <span className="text-sm font-medium text-bear">Analysis Failed</span>
          </div>
          <p className="text-xs font-mono text-muted-foreground">{decision.error_message}</p>
        </div>
      )}
    </div>
  );
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function Metric({
  label,
  value,
  valueClass = "text-foreground",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div>
      <p className="text-[11px] text-muted-foreground mb-0.5">{label}</p>
      <p className={cn("font-mono text-sm font-medium tabular-nums", valueClass)}>{value}</p>
    </div>
  );
}

function ArbiterVerdictBlock({
  signal,
  reasoning,
}: {
  signal: string;
  reasoning: string;
}) {
  return (
    <div className={cn(
      "glass-card p-5 border",
      signal === "BUY"  && "border-bull/30 bg-bull-bg/30",
      signal === "SELL" && "border-bear/30 bg-bear-bg/30",
      signal === "HOLD" && "border-hold/30 bg-hold-bg/30",
    )}>
      <div className="flex items-center gap-2 mb-4">
        <Scale className="w-4 h-4 text-muted-foreground" />
        <span className="text-sm font-medium">Arbiter Verdict</span>
        <SignalPill signal={signal as any} size="sm" />
      </div>

      {/* Reasoning paragraphs */}
      <div className="space-y-3">
        {reasoning.split("\n\n").filter(Boolean).map((paragraph, i) => (
          <p key={i} className={cn(
            "text-sm leading-relaxed",
            paragraph.startsWith("[RULE ENGINE]")
              ? "text-hold/80 font-mono text-xs border-l-2 border-hold/40 pl-3"
              : "text-foreground/90"
          )}>
            {paragraph}
          </p>
        ))}
      </div>
    </div>
  );
}

function ThesisBlock({
  side,
  thesis,
  confidence,
  sources,
}: {
  side: "bull" | "bear";
  thesis: string;
  confidence: number;
  sources: SourceCitation[];
}) {
  const isBull = side === "bull";
  const Icon = isBull ? TrendingUp : TrendingDown;
  const label = isBull ? "Bull Agent" : "Bear Agent";
  const accentClass = isBull ? "text-bull border-bull/30" : "text-bear border-bear/30";
  const bgClass = isBull ? "bg-bull-bg/20" : "bg-bear-bg/20";

  return (
    <div className={cn("glass-card p-5 flex flex-col gap-4 border", accentClass, bgClass)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={cn("w-4 h-4", isBull ? "text-bull" : "text-bear")} />
          <span className="text-sm font-semibold">{label}</span>
        </div>
        <span className={cn("text-xs font-mono font-bold px-2 py-0.5 rounded border", accentClass)}>
          {formatConfidence(confidence)}
        </span>
      </div>

      {/* Thesis text */}
      {thesis ? (
        <div className="space-y-3">
          {thesis.split("\n\n").filter(Boolean).map((p, i) => (
            <p key={i} className="text-sm text-foreground/85 leading-relaxed">{p}</p>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground italic">No thesis available.</p>
      )}

      {/* Sources */}
      {sources.length > 0 && (
        <div className="pt-3 border-t border-border/60 space-y-2">
          <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <Newspaper className="w-3 h-3" />
            <span>Sources cited ({sources.length})</span>
          </div>
          <div className="space-y-1.5">
            {sources.slice(0, 4).map((src, i) => (
              <SourceCard key={i} source={src} />
            ))}
            {sources.length > 4 && (
              <p className="text-[10px] text-muted-foreground pl-1">
                +{sources.length - 4} more sources
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function SourceCard({ source }: { source: SourceCitation }) {
  const content = (
    <div className="flex items-start gap-2 p-2 rounded bg-surface-3/60 hover:bg-surface-3 transition-colors">
      <Database className="w-3 h-3 text-muted-foreground/50 shrink-0 mt-0.5" />
      <div className="min-w-0">
        <p className="text-[11px] text-foreground/80 leading-snug line-clamp-2">
          {source.title}
        </p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] text-muted-foreground">{source.source}</span>
          {source.sentiment != null && (
            <span className={cn(
              "text-[10px] font-mono",
              source.sentiment >= 0.1  ? "text-bull" :
              source.sentiment <= -0.1 ? "text-bear" :
              "text-muted-foreground"
            )}>
              {source.sentiment >= 0 ? "+" : ""}{source.sentiment.toFixed(2)}
            </span>
          )}
          {source.url && <ExternalLink className="w-2.5 h-2.5 text-muted-foreground/40" />}
        </div>
        {source.relevance && (
          <p className="text-[10px] text-muted-foreground/60 italic mt-0.5 line-clamp-1">
            {source.relevance}
          </p>
        )}
      </div>
    </div>
  );

  return source.url ? (
    <a href={source.url} target="_blank" rel="noopener noreferrer" className="block">
      {content}
    </a>
  ) : (
    <div>{content}</div>
  );
}
