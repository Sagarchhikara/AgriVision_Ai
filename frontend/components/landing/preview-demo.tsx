"use client";

import { CheckCircle2, CircleHelp, ShieldAlert } from "lucide-react";
import Image from "next/image";
import { useState } from "react";

import { useI18n } from "@/components/i18n-provider";
import {
  IllustrativeBadge,
  PredictionRows,
  SAMPLE_LIKELY,
  SAMPLE_UNCERTAIN,
} from "@/components/landing/shared";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Wordmark } from "@/components/wordmark";
import { classLabel } from "@/lib/classes";
import { formatPercent } from "@/lib/format";
import type { LandingDictionary } from "@/lib/i18n/landing/en";
import { cn } from "cn";
import gradcam from "@/assets/landing/lesions-gradcam.jpg";
import modelView from "@/assets/landing/lesions-model-view.jpg";

type Variant = "likely" | "uncertain";

function Toggle<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <div
      role="group"
      aria-label={label}
      className="grid auto-cols-fr grid-flow-col gap-1 rounded-lg bg-muted p-1"
    >
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "min-h-11 rounded-md px-2 text-sm font-medium transition-colors",
            value === option.value
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

/**
 * Mirrors the real result screen, including its rules: the AI notice is always
 * present, an uncertain result names no disease and shows no urgency, and advice
 * sits under "if your officer confirms this". All values are samples.
 */
export function PreviewDemo({
  preview,
  illustrative,
}: {
  preview: LandingDictionary["preview"];
  illustrative: string;
}) {
  const { t, locale } = useI18n();
  const [variant, setVariant] = useState<Variant>("likely");
  const [focus, setFocus] = useState(false);

  const uncertain = variant === "uncertain";
  const rows = uncertain ? SAMPLE_UNCERTAIN : SAMPLE_LIKELY;
  const top = rows[0]!;
  const label = classLabel(top.className, t);

  return (
    <div className="overflow-hidden rounded-2xl bg-background text-foreground shadow-2xl">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-card px-4 py-3 sm:px-6">
        <Wordmark name={t.app.name} />
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="healthy">
            <CheckCircle2 aria-hidden />
            {preview.status}
          </Badge>
          <IllustrativeBadge label={illustrative} />
        </div>
      </div>

      <div className="grid gap-6 p-4 sm:p-6 lg:grid-cols-12 lg:gap-8">
        <div className="flex flex-col gap-3 lg:col-span-4">
          <div className="relative aspect-square overflow-hidden rounded-xl border bg-muted">
            <Image
              src={focus ? gradcam : modelView}
              alt={focus ? t.result.focusAlt : t.result.photoAlt}
              fill
              sizes="(min-width: 1024px) 360px, 100vw"
              className="object-cover"
            />
          </div>
          <Toggle
            label={t.result.viewToggle}
            value={focus ? "focus" : "photo"}
            options={[
              { value: "photo", label: t.result.showPhoto },
              { value: "focus", label: t.result.showFocus },
            ]}
            onChange={(next) => setFocus(next === "focus")}
          />
          <p className="text-sm text-muted-foreground">{t.result.focusExplanation}</p>
        </div>

        <div className="flex flex-col gap-4 lg:col-span-4">
          <Toggle
            label={preview.variantLabel}
            value={variant}
            options={[
              { value: "likely", label: preview.likely },
              { value: "uncertain", label: preview.uncertain },
            ]}
            onChange={setVariant}
          />

          <Alert role="note" variant="warning">
            <ShieldAlert aria-hidden />
            <AlertTitle>{t.disclaimer.title}</AlertTitle>
            <AlertDescription>{t.disclaimer.body}</AlertDescription>
          </Alert>

          {/* Announces the change of example to screen readers. */}
          <div aria-live="polite">
            {uncertain ? (
              <>
                <h3 className="flex items-center gap-2 font-heading text-h2">
                  <CircleHelp aria-hidden className="size-6 shrink-0 text-[var(--accent-text)]" />
                  {t.result.uncertainTitle}
                </h3>
                <p className="mt-1 text-muted-foreground">{t.result.uncertainBody}</p>
              </>
            ) : (
              <>
                <p className="text-sm font-medium text-muted-foreground">
                  {t.result.likelyEyebrow}
                </p>
                <h3 className="font-heading text-h2">
                  {label.condition}
                  <span className="ml-2 text-base font-normal text-muted-foreground">
                    {label.crop}
                  </span>
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {t.result.confidenceLine}{" "}
                  <span className="font-semibold text-foreground tabular-nums">
                    {formatPercent(top.confidence, locale)}
                  </span>
                </p>
              </>
            )}
          </div>

          <div className="rounded-xl border bg-card p-4">
            <h3 className="font-heading text-h3">{t.result.possibleMatches}</h3>
            <p className="mb-3 text-sm text-muted-foreground">{t.result.possibleMatchesNote}</p>
            <PredictionRows rows={rows} t={t} locale={locale} emphasizeFirst={!uncertain} />
          </div>
        </div>

        <div className="flex flex-col gap-4 lg:col-span-4">
          <h3 className="font-heading text-h2">{t.report.heading}</h3>
          {uncertain ? (
            <>
              <section>
                <h4 className="font-semibold">{t.result.betterPhotoTitle}</h4>
                <p className="mt-1 text-muted-foreground">{t.result.betterPhotoBody}</p>
              </section>
              <Alert role="note" variant="warning">
                <ShieldAlert aria-hidden />
                <AlertDescription>{t.report.chemicalUncertain}</AlertDescription>
              </Alert>
            </>
          ) : (
            <>
              <section>
                <h4 className="font-semibold">{t.report.summary}</h4>
                <p className="mt-1 text-muted-foreground">{preview.summary}</p>
              </section>
              <section>
                <h4 className="font-semibold">{t.report.symptoms}</h4>
                <ul className="mt-1 list-disc pl-5 text-muted-foreground">
                  {preview.signs.map((sign) => (
                    <li key={sign}>{sign}</li>
                  ))}
                </ul>
              </section>
              <section className="rounded-xl border bg-card p-4">
                <h4 className="font-semibold">{t.report.ifConfirmed}</h4>
                <ul className="mt-1 list-disc pl-5 text-muted-foreground">
                  {preview.steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ul>
                <p className="mt-3 text-sm text-muted-foreground">{t.report.chemicalNote}</p>
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
