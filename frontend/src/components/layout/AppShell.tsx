import { cn } from "@/lib/utils";
import { Brain, LayoutDashboard, Radar, Send, SlidersHorizontal } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/dashboard", label: "Deal Flow", icon: LayoutDashboard },
  { to: "/sourcing", label: "Sourcing", icon: Radar },
  { to: "/apply", label: "Apply", icon: Send },
  { to: "/thesis", label: "Thesis", icon: SlidersHorizontal },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 flex w-60 flex-col border-r border-border bg-surface">
        <div className="flex items-center gap-2.5 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/15">
            <Brain className="h-5 w-5 text-accent-soft" />
          </div>
          <div>
            <div className="text-sm font-semibold leading-tight">The VC Brain</div>
            <div className="text-[11px] text-faint">$100K in 24 hours</div>
          </div>
        </div>
        <nav className="flex flex-col gap-1 px-3 py-2">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive ? "bg-raised text-ink" : "text-muted hover:text-ink hover:bg-raised/60",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-5 py-4 text-[11px] leading-relaxed text-faint">
          Three independent axes · never averaged. Evidence-traced. Gaps disclosed.
        </div>
      </aside>

      {/* Main */}
      <main className="ml-60 flex-1">
        <div className="mx-auto max-w-[1400px] px-8 py-7">{children}</div>
      </main>
    </div>
  );
}
