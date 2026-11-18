"use client";

import { useCallback, useEffect, useState } from "react";

import { generateReport, type Language, type PredictResponse, type Report } from "@/lib/api";
import { errorCodeOf, type AppErrorCode } from "@/lib/errors";

export type ReportState =
  | { status: "loading" }
  | { status: "ready"; report: Report }
  | { status: "error"; code: AppErrorCode };

interface Settled {
  prediction: PredictResponse;
  language: Language;
  attempt: number;
  state: ReportState;
}

/**
 * Fetches the report for a prediction, separately from /predict so the result
 * can render without waiting for the LLM. A settled answer only counts for the
 * exact request it belongs to; anything else reads as loading, which covers a
 * new prediction, a language change, and a retry without resetting state.
 */
export function useReport(prediction: PredictResponse, language: Language) {
  const [attempt, setAttempt] = useState(0);
  const [settled, setSettled] = useState<Settled | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const settle = (state: ReportState) => setSettled({ prediction, language, attempt, state });

    generateReport(
      {
        predicted_class: prediction.prediction,
        confidence: prediction.confidence,
        top_k: prediction.top_predictions,
        language,
      },
      { signal: controller.signal },
    )
      .then(({ report }) => settle({ status: "ready", report }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) settle({ status: "error", code: errorCodeOf(error) });
      });

    return () => controller.abort();
  }, [prediction, language, attempt]);

  const current =
    settled?.prediction === prediction &&
    settled.language === language &&
    settled.attempt === attempt;

  const retry = useCallback(() => setAttempt((value) => value + 1), []);

  return { state: current ? settled.state : ({ status: "loading" } as const), retry };
}
