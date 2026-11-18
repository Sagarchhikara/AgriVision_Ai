"use client";

import { ShieldAlert } from "lucide-react";

import { useI18n } from "@/components/i18n-provider";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

/** Shown on every result, whatever the confidence. */
export function Disclaimer() {
  const { t } = useI18n();
  return (
    <Alert role="note" variant="warning">
      <ShieldAlert aria-hidden />
      <AlertTitle>{t.disclaimer.title}</AlertTitle>
      <AlertDescription>{t.disclaimer.body}</AlertDescription>
    </Alert>
  );
}
