import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { useLogin } from "@/api/hooks";
import { useAuthStore } from "@/store/authStore";
import { getApiErrorMessage } from "@/api/client";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const navigate = useNavigate();
  const location = useLocation();
  const { mutate: login, isPending, error } = useLogin();

  if (isAuthenticated) {
    const from = (location.state as { from?: string } | null)?.from ?? "/";
    return <Navigate to={from} replace />;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    login(
      { email, password },
      {
        onSuccess: () => {
          const from = (location.state as { from?: string } | null)?.from ?? "/";
          navigate(from, { replace: true });
        },
      }
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 text-white">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/20 shadow-glow">
            <ShieldCheck className="h-7 w-7 text-accent-soft" />
          </div>
          <h1 className="text-lg font-semibold">FraudShield AI</h1>
          <p className="mt-1 text-sm text-gray-500">Sign in to the analyst console</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-2xl border border-border-subtle bg-background-surface p-6"
        >
          <div>
            <label htmlFor="email" className="mb-1.5 block text-xs font-medium text-gray-400">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-border-subtle bg-background px-3 py-2 text-sm text-white placeholder-gray-600 outline-none focus:border-accent"
              placeholder="analyst@fraudshield.ai"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1.5 block text-xs font-medium text-gray-400">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-border-subtle bg-background px-3 py-2 text-sm text-white placeholder-gray-600 outline-none focus:border-accent"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="rounded-lg border border-risk-critical/30 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
              {getApiErrorMessage(error)}
            </p>
          )}

          <button
            type="submit"
            disabled={isPending}
            className="w-full rounded-lg bg-accent px-3 py-2.5 text-sm font-medium text-white transition-colors hover:bg-accent-soft disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isPending ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
