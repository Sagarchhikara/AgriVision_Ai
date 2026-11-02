"use client";

import { useEffect, useState } from "react";

import { ApiError, getHealth, type HealthResponse } from "@/lib/api";

type State =
  { kind: "loading" } | { kind: "ok"; health: HealthResponse } | { kind: "error"; message: string };

export function ConnectionCheck() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    getHealth({ signal: controller.signal })
      .then((health) => setState({ kind: "ok", health }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          error instanceof ApiError ? `${error.code}: ${error.message}` : String(error);
        setState({ kind: "error", message });
      });
    return () => controller.abort();
  }, []);

  return (
    <p className="mt-4" role="status">
      {state.kind === "loading" && "Checking backend…"}
      {state.kind === "ok" &&
        `Backend ${state.health.status}, model loaded: ${state.health.model_loaded ? "yes" : "no"}, v${state.health.version}`}
      {state.kind === "error" && `Backend unreachable (${state.message})`}
    </p>
  );
}
