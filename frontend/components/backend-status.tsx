"use client";

import { ErrorAlert } from "@/components/error-alert";
import { useHealth } from "@/hooks/use-health";

/** Warns before the user spends time on a photo that can't be checked. Silent when healthy. */
export function BackendStatus() {
  const { state, recheck } = useHealth();
  if (state.status !== "down") return null;
  return <ErrorAlert code={state.code} onRetry={recheck} />;
}
