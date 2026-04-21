"use client";
import { useState } from "react";
import { Search, Zap, Bell } from "lucide-react";
import { runAnalysis } from "@/lib/api";
import { useAgentStore } from "@/store/agentStore";
import { cn } from "@/lib/utils";

export function Topbar() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [flash, setFlash] = useState(false);

  const handleRun = async () => {
    if (!ticker.trim() || loading) return;
    setLoading(true);
    try {
      await runAnalysis(ticker.toUpperCase());
      setFlash(true);
      setTicker("");
      setTimeout(() => setFlash(false), 600);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <header className="h-14 flex items-center gap-4 px-6 border-b border-border bg-surface-1/80 backdrop-blur-sm">
      {/* Analysis input */}
      <div className={cn(
        "flex items-center gap-2 rounded-lg border px-3 py-1.5 bg-surface-0 transition-all w-64",
        flash ? "border-cyber/60 shadow-glow-cyber" : "border-border"
      )}>
        <Search className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
        <input
          type="text"
          placeholder="TSLA, AAPL, BTC-USD…"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleRun()}
          className="bg-transparent text-sm outline-none w-full text-foreground placeholder:text-muted-foreground font-mono"
        />
      </div>

      <button
        onClick={handleRun}
        disabled={!ticker.trim() || loading}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
          "bg-cyber/10 border border-cyber/30 text-cyber hover:bg-cyber/20",
          "disabled:opacity-40 disabled:cursor-not-allowed"
        )}
      >
        <Zap className={cn("w-3.5 h-3.5", loading && "animate-pulse")} />
        {loading ? "Queuing…" : "Run Swarm"}
      </button>

      <div className="flex-1" />

      {/* Notifications */}
      <button className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-2 transition-colors">
        <Bell className="w-4 h-4" />
      </button>

      {/* User avatar placeholder */}
      <div className="w-7 h-7 rounded-full bg-cyber/20 border border-cyber/30 flex items-center justify-center">
        <span className="text-cyber text-[10px] font-bold">U</span>
      </div>
    </header>
  );
}
