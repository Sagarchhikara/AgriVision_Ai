"use client";

import Image from "next/image";
import { useState } from "react";

import { useI18n } from "@/components/i18n-provider";
import { cn } from "cn";

type View = "original" | "model" | "focus";

/**
 * The photo as submitted, then the model's view of it, then the Grad-CAM
 * overlay. The last two are the same centred square crop (see
 * MODEL_CROP_FRACTION), so toggling between them keeps the leaf in place.
 */
export function PhotoWithHeatmap({
  originalUrl,
  photoUrl,
  heatmap,
}: {
  originalUrl: string;
  photoUrl: string;
  heatmap: string;
}) {
  const { t } = useI18n();
  const [view, setView] = useState<View>("model");

  const views: Record<View, { label: string; src: string; alt: string }> = {
    original: { label: t.result.showOriginal, src: originalUrl, alt: t.upload.previewAlt },
    model: { label: t.result.showPhoto, src: photoUrl, alt: t.result.photoAlt },
    focus: { label: t.result.showFocus, src: heatmap, alt: t.result.focusAlt },
  };

  return (
    <section aria-labelledby="photo-heading" className="flex flex-col gap-3">
      <h2 id="photo-heading" className="sr-only">
        {t.result.photoHeading}
      </h2>
      <div className="relative mx-auto aspect-square w-full max-w-sm overflow-hidden rounded-xl border bg-muted print:max-w-56">
        <Image
          src={views[view].src}
          alt={views[view].alt}
          fill
          unoptimized
          sizes="(max-width: 448px) 100vw, 384px"
          className={view === "original" ? "object-contain" : "object-cover"}
        />
      </div>
      <div
        role="group"
        aria-label={t.result.viewToggle}
        className="mx-auto grid w-full max-w-sm grid-cols-3 gap-1 rounded-lg bg-muted p-1 print:hidden"
      >
        {(Object.keys(views) as View[]).map((key) => (
          <button
            key={key}
            type="button"
            aria-pressed={view === key}
            onClick={() => setView(key)}
            className={cn(
              "min-h-11 rounded-md px-1 text-sm font-medium transition-colors",
              view === key
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {views[key].label}
          </button>
        ))}
      </div>
      <p className="text-center text-sm">
        {t.result.focusExplanation} {t.result.focusNotProof}
      </p>
      <p className="text-center text-sm text-muted-foreground">{t.result.centreNote}</p>
    </section>
  );
}
