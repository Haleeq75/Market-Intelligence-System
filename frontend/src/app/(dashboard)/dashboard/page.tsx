import { AgentStatusPanel } from "@/components/dashboard/AgentStatusPanel";
import { ActiveSwarmFeed, SignalCard } from "@/components/dashboard/LiveFeed";
import { getSignals, getJournalEntries } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  // Server-side fetch for initial data
  let signals: any[] = [];
  let recentDecisions: any[] = [];

  try {
    [signals, { items: recentDecisions }] = await Promise.all([
      getSignals({ limit: 6 }),
      getJournalEntries({ page_size: 6 }),
    ]);
  } catch {
    // Will render empty state — auth might not be set up yet
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-semibold text-foreground">Control Tower</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Real-time adversarial swarm intelligence
        </p>
      </div>

      {/* Active agents */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
            Active Analyses
          </h2>
        </div>
        <AgentStatusPanel />
      </section>

      {/* Two-column: Recent signals + Live feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent signals — 2/3 width */}
        <section className="lg:col-span-2">
          <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
            Recent Signals
          </h2>
          {signals.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
              {signals.map((s) => (
                <SignalCard key={s.id} signal={s} />
              ))}
            </div>
          ) : (
            <div className="glass-card p-8 text-center text-muted-foreground text-sm">
              No signals yet — run your first analysis above
            </div>
          )}
        </section>

        {/* Live event feed — 1/3 width */}
        <section>
          <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-3">
            Event Stream
          </h2>
          <ActiveSwarmFeed />
        </section>
      </div>

      {/* Stats bar */}
      <StatsBar total={recentDecisions.length} signals={signals} />
    </div>
  );
}

function StatsBar({ total, signals }: { total: number; signals: any[] }) {
  const buys  = signals.filter((s) => s.signal === "BUY").length;
  const sells = signals.filter((s) => s.signal === "SELL").length;
  const holds = signals.filter((s) => s.signal === "HOLD").length;

  const stats = [
    { label: "Total Decisions",  value: total,              color: "text-foreground" },
    { label: "BUY Signals",      value: buys,               color: "text-bull" },
    { label: "SELL Signals",     value: sells,              color: "text-bear" },
    { label: "HOLD Signals",     value: holds,              color: "text-hold" },
    { label: "Avg Net Conf.",    value: signals.length
        ? `${(signals.reduce((a, s) => a + Number(s.net_confidence), 0) / signals.length * 100).toFixed(1)}%`
        : "—",                                              color: "text-cyber" },
  ];

  return (
    <div className="glass-card px-6 py-4 grid grid-cols-2 sm:grid-cols-5 gap-4">
      {stats.map(({ label, value, color }) => (
        <div key={label} className="text-center">
          <p className={`metric-value text-lg ${color}`}>{value}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">{label}</p>
        </div>
      ))}
    </div>
  );
}
