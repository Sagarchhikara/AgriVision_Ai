import Image from "next/image";
import type { ReactNode } from "react";

import { Container, CornerMarks } from "@/components/landing/shared";
import type { Dictionary } from "@/lib/i18n/dictionaries/en";
import type { LandingDictionary } from "@/lib/i18n/landing/en";
import handHeldLeaf from "@/assets/landing/hand-held-leaf.jpg";
import modelView from "@/assets/landing/lesions-model-view.jpg";

const IMAGE_SIZES = "(min-width: 1024px) 380px, (min-width: 640px) 50vw, 100vw";

function Step({
  number,
  title,
  body,
  children,
}: {
  number: string;
  title: string;
  body: string;
  children: ReactNode;
}) {
  return (
    <li className="reveal flex flex-col">
      <div className="relative aspect-[4/3] overflow-hidden rounded-2xl">{children}</div>
      <div className="mt-5 flex gap-4">
        <span
          aria-hidden
          className="font-heading text-3xl leading-none font-extrabold text-[var(--accent-text)] tabular-nums"
        >
          {number}
        </span>
        <div>
          <h3 className="font-heading text-xl font-bold">{title}</h3>
          <p className="mt-1.5 leading-relaxed text-muted-foreground">{body}</p>
        </div>
      </div>
    </li>
  );
}

export function HowItWorks({ how, t }: { how: LandingDictionary["how"]; t: Dictionary }) {
  return (
    <section
      id="how-it-works"
      aria-labelledby="how-heading"
      className="bg-secondary py-20 lg:py-28"
    >
      <Container>
        <h2 id="how-heading" className="display-lg reveal max-w-3xl text-balance">
          {how.heading}
        </h2>
        <ol className="mt-12 grid gap-10 md:grid-cols-3 md:gap-6 lg:mt-16 lg:gap-8">
          <Step number="01" title={how.capture.title} body={how.capture.body}>
            <Image
              src={handHeldLeaf}
              alt={how.capture.alt}
              placeholder="blur"
              fill
              sizes={IMAGE_SIZES}
              className="object-cover"
            />
            <CornerMarks />
          </Step>

          <Step number="02" title={how.analyze.title} body={how.analyze.body}>
            <Image
              src={modelView}
              alt={how.analyze.alt}
              placeholder="blur"
              fill
              sizes={IMAGE_SIZES}
              className="object-cover"
            />
            <span aria-hidden className="graticule-photo absolute inset-0" />
          </Step>

          <Step number="03" title={how.understand.title} body={how.understand.body}>
            {/* Section titles from the real report, not sample advice. */}
            <div className="flex h-full flex-col justify-center gap-3 bg-card p-6" aria-hidden>
              {[t.report.summary, t.report.symptoms, t.report.prevention].map((heading) => (
                <div key={heading}>
                  <p className="font-heading text-sm font-bold">{heading}</p>
                  <div className="mt-1.5 h-1.5 w-full rounded-full bg-muted" />
                  <div className="mt-1 h-1.5 w-2/3 rounded-full bg-muted" />
                </div>
              ))}
            </div>
          </Step>
        </ol>
      </Container>
    </section>
  );
}
