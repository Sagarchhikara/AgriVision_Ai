"use client";

import { Check, CircleCheck, LoaderCircle } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { ErrorAlert } from "@/components/error-alert";
import { useI18n } from "@/components/i18n-provider";
import { Button } from "@/components/ui/button";
import { useClassList } from "@/hooks/use-class-list";
import { submitFeedback, type FeedbackVerdict, type PredictResponse } from "@/lib/api";
import { groupByCrop } from "@/lib/classes";
import { errorCodeOf, type AppErrorCode } from "@/lib/errors";
import { cn } from "cn";

type Status =
  { kind: "idle" } | { kind: "sending" } | { kind: "sent" } | { kind: "error"; code: AppErrorCode };

export function FeedbackForm({
  prediction,
  uncertain,
}: {
  prediction: PredictResponse;
  uncertain: boolean;
}) {
  const { t, locale } = useI18n();
  const classes = useClassList();
  const [verdict, setVerdict] = useState<FeedbackVerdict | null>(null);
  const [correctClass, setCorrectClass] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const request = useRef<AbortController | null>(null);

  useEffect(() => () => request.current?.abort(), []);

  const verdicts: { value: FeedbackVerdict; label: string }[] = [
    { value: "yes", label: t.feedback.yes },
    { value: "no", label: t.feedback.no },
    { value: "unsure", label: t.feedback.notSure },
  ];

  const submit = async () => {
    if (!verdict) return;
    const controller = new AbortController();
    request.current = controller;
    setStatus({ kind: "sending" });
    try {
      await submitFeedback(
        {
          predicted_class: prediction.prediction,
          confidence: prediction.confidence,
          top_k: prediction.top_predictions,
          verdict,
          // The backend rejects a correction alongside a "yes".
          correct_class: verdict !== "yes" && correctClass ? correctClass : null,
          language: locale,
        },
        { signal: controller.signal },
      );
      setStatus({ kind: "sent" });
    } catch (error) {
      if (!controller.signal.aborted) setStatus({ kind: "error", code: errorCodeOf(error) });
    }
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void submit();
  };

  const sending = status.kind === "sending";
  const sent = status.kind === "sent";

  return (
    <section aria-labelledby="feedback-heading" className="rounded-xl border bg-card p-4">
      <h2 id="feedback-heading" className="text-lg font-semibold">
        {uncertain ? t.feedback.titleUncertain : t.feedback.title}
      </h2>

      {/* Always mounted so the confirmation is announced when it appears. */}
      <div role="status">
        {sent && (
          <p className="mt-2 flex items-center gap-2 font-medium text-primary">
            <CircleCheck aria-hidden className="size-5 shrink-0" />
            {t.feedback.thanks}
          </p>
        )}
      </div>

      {!sent && (
        <form onSubmit={onSubmit} className="mt-1 flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">{t.feedback.intro}</p>

          <fieldset disabled={sending} className="grid grid-cols-3 gap-2">
            <legend className="sr-only">
              {uncertain ? t.feedback.titleUncertain : t.feedback.title}
            </legend>
            {verdicts.map(({ value, label }) => (
              <label
                key={value}
                className={cn(
                  "flex min-h-12 cursor-pointer items-center justify-center gap-1.5 rounded-lg border border-input px-2 text-center text-sm font-medium transition-colors has-focus-visible:ring-3 has-focus-visible:ring-ring/50",
                  verdict === value
                    ? "border-primary bg-secondary text-secondary-foreground"
                    : "bg-card hover:bg-muted",
                )}
              >
                <input
                  type="radio"
                  name="verdict"
                  value={value}
                  checked={verdict === value}
                  onChange={() => setVerdict(value)}
                  className="sr-only"
                />
                {verdict === value && <Check aria-hidden className="size-4 shrink-0" />}
                {label}
              </label>
            ))}
          </fieldset>

          {verdict && verdict !== "yes" && classes && (
            <div className="flex flex-col gap-1.5">
              <label htmlFor="correct-class" className="text-sm font-medium">
                {t.feedback.correctClassLabel}
              </label>
              {/* Native on purpose: it opens the phone's own picker and costs no JavaScript. */}
              <select
                id="correct-class"
                value={correctClass}
                disabled={sending}
                onChange={(event) => setCorrectClass(event.target.value)}
                className="h-12 w-full rounded-lg border border-input bg-card px-3 text-base focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
              >
                <option value="">{t.feedback.correctClassNone}</option>
                {groupByCrop(classes, t, locale).map(({ crop, options }) => (
                  <optgroup key={crop} label={crop}>
                    {options.map(({ className, condition }) => (
                      <option key={className} value={className}>
                        {condition}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
          )}

          {status.kind === "error" && <ErrorAlert code={status.code} />}

          <Button type="submit" disabled={!verdict || sending}>
            {sending && (
              <LoaderCircle aria-hidden className="animate-spin motion-reduce:animate-none" />
            )}
            {sending ? t.feedback.sending : t.feedback.submit}
          </Button>
        </form>
      )}
    </section>
  );
}
