"use client";

import { useEffect, useState } from "react";

import { getMeta } from "@/lib/api";

/**
 * The model's class list from GET /meta, or null until it arrives. Failure also
 * stays null: the list only feeds an optional dropdown, so the feedback form
 * simply goes without it rather than showing an error.
 */
export function useClassList(): string[] | null {
  const [classes, setClasses] = useState<string[] | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getMeta({ signal: controller.signal })
      .then((meta) => setClasses(meta.classes))
      .catch(() => {});
    return () => controller.abort();
  }, []);

  return classes;
}
