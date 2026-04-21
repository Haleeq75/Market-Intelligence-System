"use client";
import { useAgentStore } from "@/store/agentStore";
import { SignalPill, ConfidenceBar, AssetBadge } from "@/components/shared";
import { cn, getStatusLabel, isRunning, timeAgo } from "@/lib/utils";
import { Radio, CheckCircle2, AlertCircle, Clock } from "lucide-react";
import type { AgentStatus } from "@/types";

const STEPS = [
  { key: "ear",     label: "Data Ear",   statusKey: "running_ear" },
  { key: "bull",    label: "Bull Agent", statusKey: "running_bull" },
  { key: "bear",    label: "Bear Agent", statusKey: "running_bear" },
  { key: "arbiter", label: "Arbiter",    statusKey: "running_arbiter" },
];

const STEP_ORDER = ["running_ear", "running_bull", "running_bear", "running_arbiter", "complete"];

function getStepState(stepStatusKey: string, currentStatus: string) {
  const currentIdx = STEP_ORDER.indexOf(currentStatus);
  const stepIdx = STEP_ORDER.indexOf(stepStatusKey);
  if (currentStatus === "error") return "error";
  if (stepStatusKey === currentStatus) return "active";
  if (stepIdx < currentIdx) return "done";
  return "pending";
}

function AgentCard({ agent }: { agent: AgentStatus }) {
  const running = isRunning(agent.status);

  return (
    <div className={cn(
      "glass-card p-4 transition-all duration-300",
      running && "gradient-border scan-overlay",
      agent.status === "complete" && "border-bull/20",
      agent.status === "error" && "border-bear/20",
    )}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <AssetBadge ticker={agent.ticker} />
          {running && <Radio className="w-3 h-3 text-cyber animate-pulse" />}
          {agent.status === "complete" && <CheckCircle2 className="w-3.5 h-3.5 text-bull" />}
          {agent.status === "error" && <AlertCircle className="w-3.5 h-3.5 text-bear" />}
        </div>
        {agent.signal && <SignalPill signal={agent.signal} size="sm" />}
      </div>

      {/* Pipeline steps */}
      <div className="flex items-center gap-1 mb-3">
        {STEPS.map((step, i) => {
          const state = getStepState(step.statusKey, agent.status);
          return (
            <div key={step.key} className="flex items-center gap-1 flex-1">
              <div className="flex flex-col items-center gap-0.5 flex-1">
                <div className={cn(
                  "w-full h-1 rounded-full transition-all duration-500",
                  state === "done"    && "bg-bull/60",
                  state === "active"  && "bg-cyber animate-pulse-slow",
                  state === "pending" && "bg-surface-3",
                  state === "error"   && "bg-bear/40",
                )} />
                <span className={cn(
                  "text-[9px] font-mono leading-none",
                  state === "done"   && "text-bull/70",
                  state === "active" && "text-cyber",
                  state === "pending"&& "text-muted-foreground/40",
                  state === "error"  && "text-bear/60",
                )}>
                  {step.label.split(" ")[0]}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Status message */}
      <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
        {agent.last_message}
      </p>

      {/* Confidence bars (when complete) */}
      {agent.status === "complete" && agent.bull_confidence != null && agent.bear_confidence != null && (
        <ConfidenceBar
          bull={agent.bull_confidence}
          bear={agent.bear_confidence}
          className="mt-3 pt-3 border-t border-border"
        />
      )}

      {/* Timestamp */}
      <div className="flex items-center gap-1 mt-2 text-[10px] text-muted-foreground/60">
        <Clock className="w-2.5 h-2.5" />
        {timeAgo(new Date(agent.updated_at).toISOString())}
      </div>
    </div>
  );
}

export function AgentStatusPanel() {
  const { activeAgents } = useAgentStore();
  const agents = Object.values(activeAgents).sort((a, b) => b.updated_at - a.updated_at);

  if (agents.length === 0) {
    return (
      <div className="glass-card p-6 flex flex-col items-center justify-center text-center min-h-[140px]">
        <Radio className="w-8 h-8 text-muted-foreground/30 mb-2" />
        <p className="text-sm text-muted-foreground">No active analyses</p>
        <p className="text-xs text-muted-foreground/60 mt-1">Use the search bar above to run the swarm on any asset</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
      {agents.map((agent) => (
        <AgentCard key={agent.decision_id} agent={agent} />
      ))}
    </div>
  );
}
