"use client";

import { Camera, CircleHelp, ImageOff, ScanSearch } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { startTransition } from "react";

import { useI18n } from "@/components/i18n-provider";
import { Disclaimer } from "@/components/result/disclaimer";
import { PhotoWithHeatmap } from "@/components/result/photo-with-heatmap";
import { TopPredictions } from "@/components/result/top-predictions";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { classLabel } from "@/lib/classes";
import { formatPercent } from "@/lib/format";
import { useAnalysis } from "@/state/analysis-context";

export function ResultScreen() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const { photo, prediction, setPhoto } = useAnalysis();

  if (!photo || !prediction) return <EmptyResult />;

  // Clearing and navigating in one transition commits them together, so this
  // page never flashes its empty state on the way out.
  const startOver = () =>
    startTransition(() => {
      setPhoto(null);
      router.push("/");
    });

  const uncertain = prediction.is_low_confidence;
  const top = classLabel(prediction.prediction, t);
  const photoView = <PhotoWithHeatmap photoUrl={photo.modelViewUrl} heatmap={prediction.heatmap} />;
  const matches = (
    <TopPredictions predictions={prediction.top_predictions} emphasizeFirst={!uncertain} />
  );

  return (
    <div className="flex flex-col gap-6">
      <Disclaimer />

      {uncertain ? (
        <>
          <header>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
              <CircleHelp aria-hidden className="size-7 shrink-0 text-warning-foreground" />
              {t.result.uncertainTitle}
            </h1>
            <p className="mt-2">{t.result.uncertainBody}</p>
          </header>
          <Alert role="note" variant="warning">
            <Camera aria-hidden />
            <AlertTitle>{t.result.betterPhotoTitle}</AlertTitle>
            <AlertDescription>
              <p>{t.result.betterPhotoBody}</p>
              <Button size="sm" variant="outline" className="mt-2 bg-card" onClick={startOver}>
                {t.result.tryAnotherPhoto}
              </Button>
            </AlertDescription>
          </Alert>
          {matches}
          {photoView}
        </>
      ) : (
        <>
          <header>
            <p className="font-medium text-muted-foreground">{t.result.likelyEyebrow}</p>
            <h1 className="text-3xl font-semibold tracking-tight">{top.condition}</h1>
            {top.crop && <p className="text-lg text-muted-foreground">{top.crop}</p>}
            <p className="mt-3">
              {t.result.confidenceLine}{" "}
              <strong className="tabular-nums">
                {formatPercent(prediction.confidence, locale)}
              </strong>
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{t.result.canBeWrong}</p>
          </header>
          {photoView}
          {matches}
        </>
      )}

      <Button size="lg" variant="outline" onClick={startOver}>
        <ScanSearch aria-hidden />
        {t.result.analyzeAnother}
      </Button>
    </div>
  );
}

function EmptyResult() {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-center gap-4 py-12 text-center">
      <ImageOff aria-hidden className="size-12 text-muted-foreground" />
      <h1 className="text-2xl font-semibold">{t.result.emptyTitle}</h1>
      <p className="text-muted-foreground">{t.result.emptyBody}</p>
      <Button asChild size="lg">
        <Link href="/">{t.result.emptyAction}</Link>
      </Button>
    </div>
  );
}
