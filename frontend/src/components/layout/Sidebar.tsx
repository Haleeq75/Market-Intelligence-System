"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, BookOpen, TrendingUp, Settings, Radio, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAgentStore } from "@/store/agentStore";

const NAV = [
  { href: "/dashboard", label: "Control Tower", icon: LayoutDashboard },
  { href: "/signals",   label: "Signals",       icon: TrendingUp },
  { href: "/journal",   label: "Decision Journal", icon: BookOpen },
  { href: "/settings",  label: "Watchlist",     icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { wsConnected, activeAgents } = useAgentStore();
  const runningCount = Object.values(activeAgents).filter(
    (a) => !["complete", "error", "pending"].includes(a.status)
  ).length;

  return (
    <aside className="fixed inset-y-0 left-0 z-40 w-56 flex flex-col bg-surface-1 border-r border-border">
      {/* Logo */}
      <div className="h-14 flex items-center gap-3 px-4 border-b border-border">
        <div className="relative w-7 h-7">
          <div className="absolute inset-0 rounded bg-cyber/20 border border-cyber/40 flex items-center justify-center">
            <span className="text-cyber text-xs font-bold font-mono">AS</span>
          </div>
        </div>
        <div>
          <p className="text-[11px] font-semibold tracking-widest text-muted-foreground uppercase">
            Adversarial
          </p>
          <p className="text-[13px] font-bold text-foreground leading-none">Swarm</p>
        </div>
      </div>

      {/* Connection status */}
      <div className="px-4 py-2 border-b border-border">
        <div className="flex items-center gap-2 text-[11px]">
          <span className={cn(
            "w-1.5 h-1.5 rounded-full",
            wsConnected ? "bg-bull animate-pulse-slow" : "bg-muted-foreground"
          )} />
          <span className="text-muted-foreground">
            {wsConnected ? "Live feed connected" : "Connecting..."}
          </span>
        </div>
        {runningCount > 0 && (
          <div className="mt-1 flex items-center gap-1.5 text-[11px] text-cyber">
            <Radio className="w-3 h-3 animate-pulse" />
            <span>{runningCount} agent{runningCount > 1 ? "s" : ""} running</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors",
                active
                  ? "bg-cyber/10 text-cyber border border-cyber/20"
                  : "text-muted-foreground hover:text-foreground hover:bg-surface-2"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom actions */}
      <div className="p-2 border-t border-border">
        <button className="w-full flex items-center gap-3 px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-surface-2 rounded-md transition-colors">
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
