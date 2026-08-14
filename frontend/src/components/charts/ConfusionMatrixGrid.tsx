import type { ConfusionMatrix } from "@/types/api";

export function ConfusionMatrixGrid({ matrix }: { matrix: ConfusionMatrix }) {
  const total =
    matrix.true_negative + matrix.false_positive + matrix.false_negative + matrix.true_positive;

  const cells = [
    {
      label: "True Negative",
      sublabel: "Correctly cleared",
      value: matrix.true_negative,
      tone: "border-risk-low/40 bg-risk-low/10 text-risk-low",
    },
    {
      label: "False Positive",
      sublabel: "False alarm",
      value: matrix.false_positive,
      tone: "border-risk-medium/40 bg-risk-medium/10 text-risk-medium",
    },
    {
      label: "False Negative",
      sublabel: "Fraud missed",
      value: matrix.false_negative,
      tone: "border-risk-critical/40 bg-risk-critical/10 text-risk-critical",
    },
    {
      label: "True Positive",
      sublabel: "Correctly flagged",
      value: matrix.true_positive,
      tone: "border-accent/40 bg-accent/10 text-accent-soft",
    },
  ];

  return (
    <div>
      <div className="grid grid-cols-2 gap-3">
        {cells.map((cell) => (
          <div key={cell.label} className={`rounded-xl border p-4 ${cell.tone}`}>
            <p className="text-2xl font-semibold">{cell.value.toLocaleString()}</p>
            <p className="mt-1 text-xs font-medium">{cell.label}</p>
            <p className="text-xs opacity-70">{cell.sublabel}</p>
          </div>
        ))}
      </div>
      <p className="mt-3 text-center text-xs text-gray-500">
        {total.toLocaleString()} test predictions total
      </p>
    </div>
  );
}
