import type { Metadata } from "next";

import { Faq } from "@/components/landing/faq";
import { Features } from "@/components/landing/features";
import { FinalCta } from "@/components/landing/final-cta";
import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingNav } from "@/components/landing/landing-nav";
import { Problem } from "@/components/landing/problem";
import { ProductPreview } from "@/components/landing/product-preview";
import { ResponsibleAi } from "@/components/landing/responsible-ai";
import { ValueStrip } from "@/components/landing/value-strip";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary, getLandingDictionary } from "@/lib/i18n/dictionaries";

export async function generateMetadata({ params }: PageProps<"/[locale]">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  const { meta } = await getLandingDictionary(locale);
  return { title: { absolute: meta.title }, description: meta.description };
}

export default async function LandingPage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) return null; // [locale]/layout.tsx has already called notFound().
  const [t, l] = await Promise.all([getDictionary(locale), getLandingDictionary(locale)]);

  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-40 focus:rounded-lg focus:bg-primary focus:px-4 focus:py-3 focus:text-primary-foreground"
      >
        {t.app.skipToContent}
      </a>
      <LandingNav nav={l.nav} />
      <main id="main" tabIndex={-1} className="outline-none">
        <Hero locale={locale} t={t} l={l} />
        <ValueStrip value={l.value} />
        <Problem problem={l.problem} />
        <HowItWorks how={l.how} t={t} />
        <Features locale={locale} t={t} l={l} />
        <ProductPreview l={l} />
        <ResponsibleAi responsible={l.responsible} />
        <Faq faq={l.faq} t={t} locale={locale} />
        <FinalCta final={l.final} locale={locale} />
      </main>
      <LandingFooter locale={locale} t={t} l={l} />
    </>
  );
}
