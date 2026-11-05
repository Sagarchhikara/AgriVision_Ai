"use client";

import Image from "next/image";
import { useState } from "react";

import { useI18n } from "@/components/i18n-provider";
import { cn } from "cn";

/**
 * The model's view of the photo, switchable to the Grad-CAM overlay. Both are
 * the same centred square crop (see MODEL_CROP_FRACTION), so toggling keeps
 * the leaf in place.
 */
export function PhotoWithHeatmap({ photoUrl, heatmap }: { photoUrl: string; heatmap: string }) {
  const { t } = useI18n();
  const [showFocus, setShowFocus] = useState(false);

  const options = [
    { focus: false, label: t.result.showPhoto },
    { focus: true, label: t.result.showFocus },
  ];

  return (
    <section aria-labelledby="photo-heading" className="flex flex-col gap-3">
      <h2 id="photo-heading" className="sr-only">
        {t.result.photoHeading}
      </h2>
      <div className="relative mx-auto aspect-square w-full max-w-sm overflow-hidden rounded-xl border bg-muted">
        <Image
          src={showFocus ? heatmap : photoUrl}
          alt={showFocus ? t.result.focusAlt : t.result.photoAlt}
          fill
          unoptimized
          sizes="(max-width: 448px) 100vw, 384px"
          className="object-cover"
        />
      </div>
      <div
        role="group"
        aria-label={t.result.viewToggle}
        className="mx-auto grid w-full max-w-sm grid-cols-2 gap-1 rounded-lg bg-muted p-1"
      >
        {options.map(({ focus, label }) => (
          <button
            key={label}
            type="button"
            aria-pressed={showFocus === focus}
            onClick={() => setShowFocus(focus)}
            className={cn(
              "h-11 rounded-md text-sm font-medium transition-colors focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none",
              showFocus === focus
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {label}
          </button>
        ))}
      </div>
      <p className="text-center text-sm">{t.result.focusExplanation}</p>
      <p className="text-center text-sm text-muted-foreground">{t.result.centreNote}</p>
    </section>
  );
}
