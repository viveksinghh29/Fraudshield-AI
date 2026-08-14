import type { LucideIcon } from "lucide-react";

export function ComingSoonPage({
  title,
  description,
  phase,
  icon: Icon,
}: {
  title: string;
  description: string;
  phase: string;
  icon: LucideIcon;
}) {
  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10">
          <Icon className="h-7 w-7 text-accent-soft" />
        </div>
        <h1 className="text-lg font-semibold text-white">{title}</h1>
        <p className="mt-2 text-sm text-gray-500">{description}</p>
        <p className="mt-4 inline-block rounded-full border border-border-subtle bg-background-surface px-3 py-1 text-xs text-gray-500">
          Coming in {phase}
        </p>
      </div>
    </div>
  );
}
