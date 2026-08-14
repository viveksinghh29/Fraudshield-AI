import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Receipt,
  UploadCloud,
  LineChart,
  Gauge,
  Sparkles,
  MessageSquareText,
  ShieldCheck,
  Settings,
  UserCircle,
  LogOut,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { useLogout } from "@/api/hooks";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/predict", label: "Single Prediction", icon: ShieldCheck },
  { to: "/batch", label: "Batch Prediction", icon: UploadCloud },
  { to: "/transactions", label: "Transactions", icon: Receipt },
  { to: "/analytics", label: "Analytics", icon: LineChart },
  { to: "/model-performance", label: "Model Performance", icon: Gauge },
  { to: "/shap", label: "SHAP Visualizations", icon: Sparkles },
  { to: "/assistant", label: "Analyst Assistant", icon: MessageSquareText },
  { to: "/profile", label: "Profile", icon: UserCircle },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppLayout({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const { mutate: logout } = useLogout();

  return (
    <div className="flex min-h-screen bg-background text-white">
      <aside className="flex w-64 flex-col border-r border-border-subtle bg-background-surface">
        <div className="flex items-center gap-3 px-6 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/20 shadow-glow">
            <span className="font-bold text-accent-soft">FS</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-wide">FraudShield AI</h1>
            <p className="text-xs text-gray-500">Analyst Console</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-2">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-accent/15 text-accent-soft"
                    : "text-gray-400 hover:bg-background-elevated hover:text-gray-200"
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border-subtle px-4 py-4">
          {user && (
            <div className="mb-3">
              <p className="truncate text-sm text-gray-200">{user.full_name}</p>
              <p className="truncate text-xs capitalize text-gray-500">{user.role}</p>
            </div>
          )}
          <button
            onClick={() => logout()}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-400 transition-colors hover:bg-background-elevated hover:text-risk-critical"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
