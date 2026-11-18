"use client";

/**
 * Holds the current photo and its prediction across the upload -> result
 * navigation. Kept in memory only: a refresh on /result shows the empty state
 * rather than persisting a photo on a shared or low-storage device.
 */

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import type { PredictResponse } from "@/lib/api";
import { releasePhoto, type PreparedPhoto } from "@/lib/image";

interface AnalysisState {
  photo: PreparedPhoto | null;
  prediction: PredictResponse | null;
  /** Kept here so changing language can't reopen the form and record a duplicate. */
  feedbackSent: boolean;
}

interface AnalysisValue extends AnalysisState {
  /** Replaces the photo (releasing the old one's object URLs) and clears its prediction. */
  setPhoto: (photo: PreparedPhoto | null) => void;
  setPrediction: (prediction: PredictResponse) => void;
  markFeedbackSent: () => void;
}

const AnalysisContext = createContext<AnalysisValue | null>(null);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AnalysisState>({
    photo: null,
    prediction: null,
    feedbackSent: false,
  });

  const { photo } = state;
  useEffect(() => {
    if (!photo) return;
    return () => releasePhoto(photo);
  }, [photo]);

  const value = useMemo<AnalysisValue>(
    () => ({
      ...state,
      setPhoto: (next) => setState({ photo: next, prediction: null, feedbackSent: false }),
      setPrediction: (prediction) =>
        setState((previous) => ({ ...previous, prediction, feedbackSent: false })),
      markFeedbackSent: () => setState((previous) => ({ ...previous, feedbackSent: true })),
    }),
    [state],
  );

  return <AnalysisContext value={value}>{children}</AnalysisContext>;
}

export function useAnalysis(): AnalysisValue {
  const value = useContext(AnalysisContext);
  if (!value) throw new Error("useAnalysis must be used inside <AnalysisProvider>.");
  return value;
}
