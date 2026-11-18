"use client";

import { LoaderCircle, ScanSearch, Trash2 } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { BackendStatus } from "@/components/backend-status";
import { ErrorAlert } from "@/components/error-alert";
import { useI18n } from "@/components/i18n-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PhotoPicker } from "@/components/upload/photo-picker";
import { PhotoTips } from "@/components/upload/photo-tips";
import { predict } from "@/lib/api";
import { errorCodeOf, type AppErrorCode } from "@/lib/errors";
import { preparePhoto } from "@/lib/image";
import { useAnalysis } from "@/state/analysis-context";

type Busy = "preparing" | "analyzing" | null;

export function UploadScreen() {
  const { t, href } = useI18n();
  const router = useRouter();
  const { photo, setPhoto, setPrediction } = useAnalysis();
  const [busy, setBusy] = useState<Busy>(null);
  const [error, setError] = useState<{ code: AppErrorCode; retry?: () => void } | null>(null);
  const request = useRef<AbortController | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => () => request.current?.abort(), []);

  const choose = async (file: File) => {
    setError(null);
    setBusy("preparing");
    try {
      setPhoto(await preparePhoto(file));
    } catch (caught) {
      setError({ code: errorCodeOf(caught) });
    } finally {
      setBusy(null);
    }
  };

  const analyze = async () => {
    if (!photo) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;

    setError(null);
    setBusy("analyzing");
    try {
      setPrediction(await predict(photo.blob, { signal: controller.signal }));
      router.push(href("/result"));
    } catch (caught) {
      if (controller.signal.aborted) return;
      setError({ code: errorCodeOf(caught), retry: analyze });
      setBusy(null);
    }
  };

  // The Remove button disappears with the photo, so focus needs somewhere to go.
  const removePhoto = () => {
    setError(null);
    setPhoto(null);
    heading.current?.focus({ preventScroll: true });
  };

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div>
        <h1 ref={heading} tabIndex={-1} className="text-h1 outline-none">
          {t.upload.title}
        </h1>
        <p className="mt-1 text-muted-foreground">{t.upload.intro}</p>
      </div>

      <BackendStatus />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem] lg:items-start">
        <div className="flex min-w-0 flex-col gap-4">
          {photo && (
            <Card asChild className="overflow-hidden">
              <figure>
                <Image
                  src={photo.url}
                  alt={t.upload.previewAlt}
                  width={photo.width}
                  height={photo.height}
                  unoptimized
                  className="max-h-[55vh] w-full object-contain"
                />
              </figure>
            </Card>
          )}

          {/* Always mounted so screen readers announce changes; sr-only (absolute)
              when idle, so it takes no space in the layout. */}
          <div role="status" className={busy ? undefined : "sr-only"}>
            {busy && (
              <p className="flex items-center gap-2 text-muted-foreground">
                <LoaderCircle
                  aria-hidden
                  className="size-5 animate-spin motion-reduce:animate-none"
                />
                {busy === "preparing" ? t.upload.preparing : t.upload.analyzing}
              </p>
            )}
          </div>

          {error && <ErrorAlert code={error.code} onRetry={error.retry} />}

          {photo && (
            <Button size="lg" onClick={analyze} disabled={busy !== null}>
              <ScanSearch aria-hidden />
              {t.upload.analyze}
            </Button>
          )}

          <div className={photo ? "grid gap-3 min-[420px]:grid-cols-2" : undefined}>
            <PhotoPicker onFile={choose} disabled={busy !== null} compact={photo !== null} />
            {photo && (
              <Button variant="outline" disabled={busy !== null} onClick={removePhoto}>
                <Trash2 aria-hidden />
                {t.upload.removePhoto}
              </Button>
            )}
          </div>
        </div>

        <PhotoTips />
      </div>
    </div>
  );
}
