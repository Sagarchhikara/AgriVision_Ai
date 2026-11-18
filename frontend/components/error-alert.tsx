"use client";

import { CircleAlert, RotateCw } from "lucide-react";

import { useI18n } from "@/components/i18n-provider";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { errorMessage, type AppErrorCode } from "@/lib/errors";

export function ErrorAlert({ code, onRetry }: { code: AppErrorCode; onRetry?: () => void }) {
  const { t } = useI18n();
  const message = errorMessage(code, t);
  return (
    <Alert variant="destructive">
      <CircleAlert aria-hidden />
      <AlertTitle>{message.title}</AlertTitle>
      <AlertDescription>
        <p>{message.body}</p>
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-2" onClick={onRetry}>
            <RotateCw aria-hidden />
            {t.errors.tryAgain}
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}
