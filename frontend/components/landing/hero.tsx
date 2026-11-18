import { ArrowRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { LanguageSwitcher } from "@/components/language-switcher";
import {
  ACCENT_BUTTON,
  Container,
  CornerMarks,
  IllustrativeBadge,
  PredictionRows,
  SAMPLE_LIKELY,
} from "@/components/landing/shared";
import { Button } from "@/components/ui/button";
import { DIAGNOSE_PATH, localePath, type Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionaries/en";
import type { LandingDictionary } from "@/lib/i18n/landing/en";
import healthyLeaf from "@/assets/landing/healthy-tomato.jpg";
import lateBlight from "@/assets/landing/hero-late-blight.jpg";

export function Hero({ locale, t, l }: { locale: Locale; t: Dictionary; l: LandingDictionary }) {
  return (
    <section aria-labelledby="hero-heading" className="overflow-x-clip">
      <Container className="grid items-center gap-12 pt-4 pb-16 lg:grid-cols-12 lg:gap-10 lg:pt-10 lg:pb-24">
        <div className="lg:col-span-6">
          {/* In the header from tablet up. A reader who needs another language
              should not have to find it inside a menu first. */}
          <div className="-mx-2 mb-6 md:hidden">
            <LanguageSwitcher />
          </div>

          <p className="eyebrow flex items-center gap-3 text-sm font-semibold text-[var(--accent-text)]">
            <span aria-hidden className="h-px w-8 bg-highlight" />
            {l.hero.eyebrow}
          </p>
          <h1 id="hero-heading" className="display-xl mt-5 text-balance">
            {l.hero.headlineLead} <span className="text-primary">{l.hero.headlineAccent}</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground sm:text-xl">
            {l.hero.body}
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <Button asChild size="lg" className={ACCENT_BUTTON}>
              <Link href={localePath(locale, DIAGNOSE_PATH)}>
                {l.hero.primaryCta}
                <ArrowRight aria-hidden />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <a href="#how-it-works">{l.hero.secondaryCta}</a>
            </Button>
          </div>

          <p className="mt-6 text-sm text-muted-foreground">{l.hero.trust}</p>
        </div>

        <figure className="relative lg:col-span-6">
          <div
            aria-hidden
            className="graticule absolute -inset-y-6 -right-40 left-[12%] -z-10 hidden lg:block"
          />

          <div className="relative mx-auto w-full max-w-[34rem] lg:mr-8 lg:ml-auto lg:w-[calc(100%-2rem)]">
            <div className="hero-plate relative aspect-[4/5] overflow-hidden rounded-2xl bg-primary shadow-card">
              <Image
                src={lateBlight}
                alt={l.hero.mainAlt}
                placeholder="blur"
                priority
                fill
                sizes="(min-width: 1024px) 544px, (min-width: 576px) 544px, 100vw"
                className="object-cover"
              />
              <CornerMarks />
              <span
                aria-hidden
                className="scan-sweep absolute inset-x-0 h-px bg-white shadow-[0_0_14px_2px_rgb(255_255_255_/_0.6)]"
              />
              {/* Sits on the lesion, which is at this spot in the crop. */}
              <span
                aria-hidden
                className="absolute top-[51%] left-[56%] aspect-square w-[24%] -translate-1/2"
              >
                <CornerMarks className="inset-0 text-[var(--harvest)]" />
              </span>
              <span className="absolute top-6 left-6 rounded-lg bg-card px-3 py-1.5 text-sm font-semibold text-foreground shadow-card">
                {l.hero.plateLabel}
              </span>
            </div>

            <div className="hero-card absolute top-3 right-3 w-24 overflow-hidden rounded-xl border-2 border-card bg-card shadow-card sm:top-20 sm:w-36 lg:top-auto lg:right-auto lg:bottom-52 lg:-left-8 lg:w-40 xl:-left-12 xl:w-44">
              <Image
                src={healthyLeaf}
                alt={l.hero.healthyAlt}
                placeholder="blur"
                className="aspect-square w-full object-cover"
                sizes="(min-width: 1024px) 176px, 144px"
              />
              <p className="px-1 py-1.5 text-center text-sm font-medium">{l.hero.healthyLabel}</p>
            </div>

            <div className="hero-card hero-card-late relative mx-3 -mt-20 rounded-xl border bg-card p-4 shadow-card lg:absolute lg:-right-8 lg:-bottom-8 lg:mx-0 lg:mt-0 lg:w-[19rem]">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <p className="font-heading text-sm font-bold">{l.hero.predictionsTitle}</p>
                <IllustrativeBadge label={l.illustrative} />
              </div>
              <PredictionRows rows={SAMPLE_LIKELY} t={t} locale={locale} />
            </div>
          </div>

          <figcaption className="mx-auto mt-4 max-w-[34rem] text-sm text-muted-foreground lg:mt-12 lg:mr-8 lg:ml-auto lg:w-[calc(100%-2rem)] lg:pr-[17rem]">
            {l.hero.caption}
          </figcaption>
        </figure>
      </Container>
    </section>
  );
}
