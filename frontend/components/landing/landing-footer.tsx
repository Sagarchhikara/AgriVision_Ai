import Link from "next/link";

import { LanguageSwitcher } from "@/components/language-switcher";
import { PHOTO_CREDITS } from "@/components/landing/photo-credits";
import { Container } from "@/components/landing/shared";
import { Wordmark } from "@/components/wordmark";
import { DIAGNOSE_PATH, localePath, type Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionaries/en";
import type { LandingDictionary } from "@/lib/i18n/landing/en";

const LINK = "inline-flex min-h-11 items-center rounded-lg hover:underline";

export function LandingFooter({
  locale,
  t,
  l,
}: {
  locale: Locale;
  t: Dictionary;
  l: LandingDictionary;
}) {
  return (
    <footer className="bg-secondary py-14">
      <Container className="grid gap-10 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <Wordmark name={t.app.name} />
          <p className="mt-3 font-heading text-lg font-bold">{l.tagline}</p>
          <p className="mt-2 max-w-md text-muted-foreground">{l.footer.description}</p>
        </div>

        <nav aria-label={l.footer.navLabel} className="lg:col-span-3">
          <ul>
            <li>
              <a href="#how-it-works" className={LINK}>
                {l.nav.howItWorks}
              </a>
            </li>
            <li>
              <a href="#features" className={LINK}>
                {l.nav.features}
              </a>
            </li>
            <li>
              <a href="#technology" className={LINK}>
                {l.nav.technology}
              </a>
            </li>
            <li>
              <a href="#faq" className={LINK}>
                {l.nav.faq}
              </a>
            </li>
            <li>
              <Link href={localePath(locale, DIAGNOSE_PATH)} className={LINK}>
                {l.nav.cta}
              </Link>
            </li>
          </ul>
        </nav>

        <div className="lg:col-span-4">
          <div className="-mx-2">
            <LanguageSwitcher label={l.footer.languageLabel} />
          </div>
          <p className="mt-4 text-sm">
            <strong className="font-semibold">{t.disclaimer.title}.</strong> {t.disclaimer.body}
          </p>
        </div>

        <div className="flex flex-col gap-3 border-t border-foreground/15 pt-6 text-sm lg:col-span-12">
          <details>
            <summary className="flex min-h-11 w-fit cursor-pointer items-center rounded-lg font-medium">
              {l.footer.credits}
            </summary>
            <p className="mb-2 text-muted-foreground">{l.footer.creditsNote}</p>
            {/* Titles and licences are the sources' own, so stay in English. */}
            <ul lang="en" className="flex flex-col gap-1 text-muted-foreground">
              {PHOTO_CREDITS.map(({ title, author, license, licenseUrl, sourceUrl }) => (
                <li key={sourceUrl}>
                  <a href={sourceUrl} rel="noreferrer" className="underline underline-offset-2">
                    {title}
                  </a>{" "}
                  by {author},{" "}
                  <a href={licenseUrl} rel="noreferrer" className="underline underline-offset-2">
                    {license}
                  </a>
                </li>
              ))}
            </ul>
          </details>
          <p className="text-muted-foreground">
            © {new Date().getFullYear()} {t.app.name}
          </p>
        </div>
      </Container>
    </footer>
  );
}
