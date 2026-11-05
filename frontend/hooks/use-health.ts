"use client";

import { useCallback, useEffect, useState } from "react";

import { getHealth } from "@/lib/api";
import { errorCodeOf, type AppErrorCode } from "@/lib/errors";

export type HealthState = { status: "checking" | "ok" } | { status: "down"; code: AppErrorCode };

/** Checks the backend when mounted, so a problem shows before the user uploads anything. */
export function useHealth() {
  const [attempt, setAttempt] = useState(0);
  const [settled, setSettled] = useState<{ attempt: number; state: HealthState } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getHealth({ signal: controller.signal })
      .then(({ model_loaded }) =>
        setSettled({
          attempt,
          state: model_loaded ? { status: "ok" } : { status: "down", code: "service_unavailable" },
        }),
      )
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setSettled({ attempt, state: { status: "down", code: errorCodeOf(error) } });
      });
    return () => controller.abort();
  }, [attempt]);

  const recheck = useCallback(() => setAttempt((value) => value + 1), []);

  return {
    state: settled?.attempt === attempt ? settled.state : ({ status: "checking" } as const),
    recheck,
  };
}
