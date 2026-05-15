import { cn } from "./ui/utils";

export interface WaterfallStep {
  label: string;
  delta: number;
}

interface WaterfallExplanationProps {
  steps: WaterfallStep[];
  baseline: number;
  className?: string;
}

/**
 * Simplified SHAP-style waterfall: baseline + deltas → final risk score (capped 0–100).
 */
export function WaterfallExplanation({
  steps,
  baseline,
  className,
}: WaterfallExplanationProps) {
  const values: { label: string; start: number; end: number; delta: number }[] =
    [];
  let cur = baseline;
  for (const s of steps) {
    const next = Math.min(100, Math.max(0, cur + s.delta));
    values.push({
      label: s.label,
      start: cur,
      end: next,
      delta: s.delta,
    });
    cur = next;
  }

  const maxVal = 100;
  const bar = (start: number, end: number) => {
    const lo = Math.min(start, end);
    const hi = Math.max(start, end);
    const left = (lo / maxVal) * 100;
    const width = Math.max((hi - lo) / maxVal, 0.02) * 100;
    return { left: `${left}%`, width: `${width}%` };
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Baseline → contributions → outcome</span>
        <span>Scale 0–100</span>
      </div>
      <div className="relative h-10 rounded-lg bg-muted/50 border border-border overflow-hidden">
        {values.map((v, i) => {
          const { left, width } = bar(v.start, v.end);
          const positive = v.delta >= 0;
          return (
            <div
              key={v.label}
              className={cn(
                "absolute top-1 bottom-1 rounded-md transition-all duration-300",
                positive
                  ? "bg-gradient-to-r from-rose-500/90 to-orange-500/85"
                  : "bg-gradient-to-r from-emerald-500/85 to-teal-500/80",
              )}
              style={{ left, width, zIndex: i + 1 }}
              title={`${v.label}: ${positive ? "+" : ""}${v.delta.toFixed(1)}`}
            />
          );
        })}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {values.map((v) => (
          <div
            key={v.label}
            className="flex items-center justify-between rounded-lg border border-border/80 bg-card/50 px-3 py-2 text-sm"
          >
            <span className="text-muted-foreground truncate pr-2">{v.label}</span>
            <span
              className={cn(
                "font-mono font-medium tabular-nums shrink-0",
                v.delta >= 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400",
              )}
            >
              {v.delta >= 0 ? "+" : ""}
              {v.delta.toFixed(1)}
            </span>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm">
        <span className="font-medium text-foreground">Explained risk score</span>
        <span className="font-mono font-semibold text-primary">
          {cur.toFixed(0)}
        </span>
      </div>
    </div>
  );
}
