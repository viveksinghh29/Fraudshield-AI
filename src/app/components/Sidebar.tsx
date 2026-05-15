import { NavLink } from "react-router";
import {
  LayoutDashboard,
  Receipt,
  Upload,
  Activity,
  Brain,
  Settings,
  Shield,
} from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", end: true },
  { to: "/transactions", icon: Receipt, label: "Transactions" },
  { to: "/upload", icon: Upload, label: "Upload CSV" },
  { to: "/real-time", icon: Activity, label: "Real-Time Detection" },
  { to: "/insights", icon: Brain, label: "Model Insights" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="w-64 shrink-0 bg-card border-r border-border flex flex-col shadow-[var(--fs-card-shadow)]">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-700 via-indigo-600 to-violet-600 flex items-center justify-center shadow-md">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="font-semibold tracking-tight text-foreground truncate">
              FraudShield AI
            </h1>
            <p className="text-xs text-muted-foreground leading-snug">
              GenAI fraud detection
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors duration-150 ${
                isActive
                  ? "bg-primary/10 text-primary font-medium shadow-sm"
                  : "text-muted-foreground hover:bg-muted/80 hover:text-foreground"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="px-4 py-3 rounded-xl bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border border-indigo-500/20">
          <p className="text-xs text-muted-foreground">Active model</p>
          <p className="text-sm font-semibold text-foreground mt-0.5">
            v2.4.1 · Random Forest
          </p>
        </div>
      </div>
    </aside>
  );
}
