import { cn } from "@/lib/utils";
import { BarChart3, Brain, LayoutDashboard, Layers, Radar, Search, Send, SlidersHorizontal } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/dashboard", label: "Deal Flow", icon: LayoutDashboard },
  { to: "/search", label: "Search", icon: Search },
  { to: "/sourcing", label: "Sourcing", icon: Radar },
  { to: "/patterns", label: "Patterns", icon: Layers },
  { to: "/channels", label: "Channels", icon: BarChart3 },
  { to: "/apply", label: "Apply", icon: Send },
  { to: "/thesis", label: "Thesis", icon: SlidersHorizontal },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="glass fixed inset-y-0 left-0 flex w-64 flex-col border-r border-white/50 shadow-soft">
        <div className="flex items-center gap-3 px-5 py-6">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-brand shadow-ring">
            <Brain className="h-5 w-5 text-white" strokeWidth={2.2} />
            <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0" />
          </div>
          <div className="leading-tight">
            <div className="font-display text-[15px] font-bold tracking-tight text-heading">
              The VC Brain
            </div>
            <div className="text-[11px] font-medium text-accent">$100K in 24 hours</div>
          </div>
        </div>

        <nav className="mt-2 flex flex-col gap-1 px-3">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition-all duration-200",
                  isActive
                    ? "bg-brand text-white shadow-ring"
                    : "text-muted hover:bg-white/70 hover:text-accent",
                )
              }
            >
              <Icon className="h-[18px] w-[18px]" strokeWidth={2.1} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto px-5 py-5">
          <div className="rounded-xl bg-brand-soft p-3.5 text-[11px] leading-relaxed text-heading/70">
            Three independent axes — never averaged. Evidence-traced. Gaps disclosed.
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="ml-64 flex-1">
        <div className="mx-auto max-w-[1440px] px-10 py-8">{children}</div>
      </main>
    </div>
  );
}
