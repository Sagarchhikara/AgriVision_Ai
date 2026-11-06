import { FileText, ShieldCheck } from "lucide-react";
import Image from "next/image";

import {
  Container,
  IllustrativeBadge,
  PredictionRows,
  SAMPLE_LIKELY,
} from "@/components/landing/shared";
import { Card } from "@/components/ui/card";
import { LOCALE_NAMES, type Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionaries/en";
import type { LandingDictionary } from "@/lib/i18n/landing/en";
import heroGradcam from "@/assets/landing/hero-gradcam.jpg";
import heroModelView from "@/assets/landing/hero-model-view.jpg";
import tomatoPlant from "@/assets/landing/tomato-plant-spots.jpg";

const TITLE = "font-heading text-xl font-bold";

/** The word "leaf" in each language, each tagged so screen readers switch voice. */
const LEAF_WORDS = [
  { lang: "en", word: "Leaf" },
  { lang: "hi", word: "पत्ती" },
  { lang: "pa", word: "ਪੱਤਾ" },
] as const;

export function Features({
  locale,
  t,
  l,
}: {
  locale: Locale;
  t: Dictionary;
  l: LandingDictionary;
}) {
  const { features } = l;
  return (
    <section id="features" aria-labelledby="features-heading" className="py-20 lg:py-28">
      <Container>
        <h2 id="features-heading" className="display-lg reveal max-w-3xl text-balance">
          {features.heading}
        </h2>

        <div className="mt-12 grid gap-5 md:grid-cols-6 lg:mt-16 lg:grid-cols-12">
          <Card className="lift reveal relative flex min-h-80 flex-col justify-end overflow-hidden border-0 md:col-span-6 lg:col-span-7">
            <Image
              src={tomatoPlant}
              alt={features.analysis.alt}
              placeholder="blur"
              fill
              sizes="(min-width: 1024px) 700px, 100vw"
              className="object-cover"
            />
            <span aria-hidden className="graticule-photo absolute inset-0" />
            <div className="relative m-3 max-w-sm rounded-xl bg-card p-5">
              <h3 className={TITLE}>{features.analysis.title}</h3>
              <p className="mt-1.5 text-muted-foreground">{features.analysis.body}</p>
            </div>
          </Card>

          <Card className="lift reveal flex flex-col gap-5 p-6 md:col-span-6 lg:col-span-5">
            <div>
              <h3 className={TITLE}>{features.breakdown.title}</h3>
              <p className="mt-1.5 text-muted-foreground">{features.breakdown.body}</p>
            </div>
            <div className="mt-auto rounded-xl bg-background p-4">
              <IllustrativeBadge label={l.illustrative} className="mb-3" />
              <PredictionRows rows={SAMPLE_LIKELY} t={t} locale={locale} />
            </div>
          </Card>

          <Card className="lift reveal flex flex-col gap-4 p-6 md:col-span-6 lg:col-span-5">
            <div className="grid grid-cols-2 gap-2">
              <figure>
                <Image
                  src={heroModelView}
                  alt={features.visuals.photoAlt}
                  placeholder="blur"
                  sizes="(min-width: 1024px) 220px, 50vw"
                  className="aspect-square w-full rounded-lg object-cover"
                />
                <figcaption className="mt-1.5 text-sm font-medium">{t.result.showPhoto}</figcaption>
              </figure>
              <figure>
                <Image
                  src={heroGradcam}
                  alt={features.visuals.focusAlt}
                  placeholder="blur"
                  sizes="(min-width: 1024px) 220px, 50vw"
                  className="aspect-square w-full rounded-lg object-cover"
                />
                <figcaption className="mt-1.5 text-sm font-medium">{t.result.showFocus}</figcaption>
              </figure>
            </div>
            <div>
              <h3 className={TITLE}>{features.visuals.title}</h3>
              <p className="mt-1.5 text-muted-foreground">{features.visuals.body}</p>
              <p className="mt-2 text-sm text-muted-foreground">{features.visuals.source}</p>
            </div>
          </Card>

          <Card
            variant="soft"
            className="lift reveal flex flex-col gap-4 p-6 md:col-span-3 lg:col-span-4"
          >
            <FileText aria-hidden className="size-7 text-primary" />
            <h3 className={TITLE}>{features.reports.title}</h3>
            <p className="text-muted-foreground">{features.reports.body}</p>
            <ul
              aria-hidden
              className="mt-auto flex flex-col gap-1 border-t border-primary/15 pt-3 text-sm font-medium"
            >
              <li>{t.report.summary}</li>
              <li>{t.report.symptoms}</li>
              <li>{t.report.consultExpert}</li>
            </ul>
          </Card>

          <Card className="lift reveal on-dark flex flex-col gap-3 border-0 bg-primary p-6 text-primary-foreground md:col-span-3 lg:col-span-3">
            <ul className="flex flex-col gap-1 font-heading text-3xl leading-snug font-extrabold">
              {LEAF_WORDS.map(({ lang, word }) => (
                <li key={lang} lang={lang}>
                  {word}
                </li>
              ))}
            </ul>
            <h3 className={`${TITLE} mt-auto`}>{features.languages.title}</h3>
            <p className="text-secondary">
              {features.languages.body}
              <span className="sr-only"> {Object.values(LOCALE_NAMES).join(", ")}</span>
            </p>
          </Card>

          <Card
            variant="muted"
            className="reveal flex flex-col gap-4 bg-card p-6 sm:flex-row sm:items-center md:col-span-6 lg:col-span-12"
          >
            <ShieldCheck aria-hidden className="size-8 shrink-0 text-primary" />
            <div>
              <h3 className={TITLE}>{features.guidance.title}</h3>
              <p className="mt-1 text-muted-foreground">{features.guidance.body}</p>
            </div>
          </Card>
        </div>
      </Container>
    </section>
  );
}
