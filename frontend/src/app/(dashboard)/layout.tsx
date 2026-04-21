import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { WsProvider } from "@/components/layout/WsProvider";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <WsProvider>
      <div className="min-h-screen bg-background flex">
        <Sidebar />
        <div className="flex-1 ml-56 flex flex-col min-h-screen">
          <Topbar />
          <main className="flex-1 p-6 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </WsProvider>
  );
}
