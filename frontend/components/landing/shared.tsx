import { FlaskConical } from "lucide-react";
import type { ComponentProps } from "react";

import { Badge } from "@/components/ui/badge";
import { classLabel } from "@/lib/classes";
import { formatPercent } from "@/lib/format";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionaries/en";
import { cn } from "cn";

/** Sample rows only: every place that shows them must also show IllustrativeBadge. */
export const SAMPLE_LIKELY = [
  { className: "Tomato___Late_blight", confidence: 0.74 },
  { className: "Tomato___Early_blight", confidence: 0.16 },
  { className: "Tomato___Septoria_leaf_spot", confidence: 0.06 },
];

/** Below the 0.60 threshold, as a real uncertain result would be. */
export const SAMPLE_UNCERTAIN = [
  { className: "Tomato___Late_blight", confidence: 0.46 },
  { className: "Tomato___Early_blight", confidence: 0.38 },
  { className: "Tomato___Septoria_leaf_spot", confidence: 0.09 },
];

/** Terracotta button. Its text colour comes from .landing in app/landing.css. */
export const ACCENT_BUTTON =
  "bg-highlight text-[var(--on-highlight)] shadow-card hover:bg-[var(--highlight-hover)]";

export function Container({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("mx-auto w-full max-w-7xl px-5 sm:px-8", className)} {...props} />;
}

export function IllustrativeBadge({ label, className }: { label: string; className?: string }) {
  return (
    <Badge variant="info" className={className}>
      <FlaskConical aria-hidden />
      {label}
    </Badge>
  );
}

/** Crop marks at the corners of a photo, as on a specimen plate. Parent must be relative. */
export function CornerMarks({ className }: { className?: string }) {
  const mark = "absolute size-5 border-current";
  return (
    <span aria-hidden className={cn("pointer-events-none absolute inset-3 text-white", className)}>
      <span className={cn(mark, "top-0 left-0 border-t-2 border-l-2")} />
      <span className={cn(mark, "top-0 right-0 border-t-2 border-r-2")} />
      <span className={cn(mark, "bottom-0 left-0 border-b-2 border-l-2")} />
      <span className={cn(mark, "right-0 bottom-0 border-r-2 border-b-2")} />
    </span>
  );
}

export function PredictionRows({
  rows,
  t,
  locale,
  emphasizeFirst = true,
}: {
  rows: readonly { className: string; confidence: number }[];
  t: Dictionary;
  locale: Locale;
  emphasizeFirst?: boolean;
}) {
  return (
    <ol className="flex flex-col gap-3">
      {rows.map(({ className, confidence }, index) => {
        const label = classLabel(className, t);
        const strong = emphasizeFirst && index === 0;
        return (
          <li key={className}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className={cn("leading-snug", strong && "font-semibold")}>
                {label.condition}
              </span>
              <span className="shrink-0 font-semibold tabular-nums">
                {formatPercent(confidence, locale)}
              </span>
            </div>
            <div aria-hidden className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className={cn(
                  "h-full rounded-full",
                  strong ? "bg-primary" : "bg-muted-foreground/50",
                )}
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
          </li>
        );
      })}
    </ol>
  );
}
