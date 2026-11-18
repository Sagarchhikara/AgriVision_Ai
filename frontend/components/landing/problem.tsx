import Image from "next/image";

import { Container } from "@/components/landing/shared";
import type { LandingDictionary } from "@/lib/i18n/landing/en";
import leafSpotsDetail from "@/assets/landing/leaf-spots-detail.jpg";
import leafSpots from "@/assets/landing/leaf-spots.jpg";

export function Problem({ problem }: { problem: LandingDictionary["problem"] }) {
  const { recognise, timing, meaning, guidance } = problem.items;
  return (
    <section aria-labelledby="problem-heading" className="py-20 lg:py-28">
      <Container>
        <h2 id="problem-heading" className="display-lg reveal max-w-4xl text-balance">
          {problem.heading}
        </h2>

        <div className="mt-12 grid items-start gap-12 lg:mt-16 lg:grid-cols-12 lg:gap-16">
          <figure className="reveal relative lg:col-span-7">
            <div className="overflow-hidden rounded-2xl">
              <Image
                src={leafSpots}
                alt={problem.imageAlt}
                placeholder="blur"
                sizes="(min-width: 1024px) 680px, 100vw"
                className="aspect-[3/2] w-full object-cover"
              />
            </div>
            {/* A loupe over the same leaf: the enlarged area is from this photo. */}
            <div className="absolute right-4 -bottom-6 size-32 overflow-hidden rounded-full border-4 border-card shadow-card sm:right-8 sm:size-44 lg:size-52">
              <Image
                src={leafSpotsDetail}
                alt={problem.detailAlt}
                placeholder="blur"
                sizes="208px"
                className="size-full object-cover"
              />
            </div>
            <figcaption className="mt-4 pr-36 text-sm text-muted-foreground sm:pr-56">
              {problem.caption}
            </figcaption>
          </figure>

          <dl className="grid gap-x-10 sm:grid-cols-2 lg:col-span-5 lg:grid-cols-1">
            {[recognise, timing, meaning, guidance].map(({ title, body }, index) => (
              <div key={title} className="reveal border-t py-5">
                <dt className="flex gap-3 font-heading text-h3">
                  <span aria-hidden className="text-[var(--accent-text)] tabular-nums">
                    {index + 1}
                  </span>
                  {title}
                </dt>
                <dd className="mt-1.5 pl-6 leading-relaxed text-muted-foreground">{body}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Container>
    </section>
  );
}
