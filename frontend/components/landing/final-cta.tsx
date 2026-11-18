import { ArrowRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { ACCENT_BUTTON, Container } from "@/components/landing/shared";
import { Button } from "@/components/ui/button";
import { DIAGNOSE_PATH, localePath, type Locale } from "@/lib/i18n/config";
import type { LandingDictionary } from "@/lib/i18n/landing/en";
import field from "@/assets/landing/field-idukki.jpg";

export function FinalCta({ final, locale }: { final: LandingDictionary["final"]; locale: Locale }) {
  return (
    <section
      aria-labelledby="final-heading"
      className="on-dark overflow-hidden bg-primary text-primary-foreground"
    >
      <Container className="grid items-center gap-10 py-20 lg:grid-cols-2 lg:gap-16 lg:py-24">
        <div className="reveal">
          <h2 id="final-heading" className="display-xl text-balance">
            {final.heading}
          </h2>
          <p className="mt-5 text-xl leading-relaxed text-secondary">{final.body}</p>
          <Button asChild size="lg" className={`${ACCENT_BUTTON} mt-8 max-sm:w-full`}>
            <Link href={localePath(locale, DIAGNOSE_PATH)}>
              {final.cta}
              <ArrowRight aria-hidden />
            </Link>
          </Button>
          <p className="mt-4 text-sm text-secondary">{final.micro}</p>
        </div>
        <div className="reveal rounded-2xl bg-secondary p-2">
          <Image
            src={field}
            alt={final.imageAlt}
            placeholder="blur"
            sizes="(min-width: 1024px) 600px, 100vw"
            className="aspect-[16/10] w-full rounded-xl object-cover"
          />
        </div>
      </Container>
    </section>
  );
}
