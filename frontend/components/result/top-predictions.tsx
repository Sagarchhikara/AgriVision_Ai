"use client";

import { useI18n } from "@/components/i18n-provider";
import { Card } from "@/components/ui/card";
import type { ClassPrediction } from "@/lib/api";
import { classLabel } from "@/lib/classes";
import { formatPercent } from "@/lib/format";
import { cn } from "cn";

/**
 * Every candidate the model returned, not just the top one, since on field
 * photos the right answer is often the second or third. Each bar is backed by
 * its percentage in text, so meaning never depends on the bar alone.
 */
export function TopPredictions({
  predictions,
  emphasizeFirst,
}: {
  predictions: ClassPrediction[];
  emphasizeFirst: boolean;
}) {
  const { t, locale } = useI18n();

  return (
    <section aria-labelledby="matches-heading" className="flex flex-col gap-3">
      <div>
        <h2 id="matches-heading" className="text-h2">
          {t.result.possibleMatches}
        </h2>
        <p className="text-sm text-muted-foreground">{t.result.possibleMatchesNote}</p>
      </div>
      <ol className="flex flex-col gap-3">
        {predictions.map((prediction, index) => {
          const label = classLabel(prediction.class_name, t);
          const strong = emphasizeFirst && index === 0;
          return (
            <Card asChild key={prediction.class_name} className="p-3">
              <li>
                <div className="flex items-baseline justify-between gap-3">
                  <p className={cn("leading-snug", strong && "font-semibold")}>
                    {label.condition}
                    {label.crop && (
                      <span className="block text-sm font-normal text-muted-foreground">
                        {label.crop}
                      </span>
                    )}
                  </p>
                  <span className="shrink-0 font-medium tabular-nums">
                    {formatPercent(prediction.confidence, locale)}
                  </span>
                </div>
                <div
                  aria-hidden
                  className="mt-2 h-2 overflow-hidden rounded-full bg-muted print:hidden"
                >
                  <div
                    className={cn(
                      "h-full rounded-full",
                      strong ? "bg-primary" : "bg-muted-foreground/50",
                    )}
                    // Capped so a saturated score never draws a bar that reads as certainty.
                    style={{ width: `${Math.min(Math.max(prediction.confidence * 100, 1), 96)}%` }}
                  />
                </div>
              </li>
            </Card>
          );
        })}
      </ol>
    </section>
  );
}
