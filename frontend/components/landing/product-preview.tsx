import { Container } from "@/components/landing/shared";
import { PreviewDemo } from "@/components/landing/preview-demo";
import type { LandingDictionary } from "@/lib/i18n/landing/en";

export function ProductPreview({ l }: { l: LandingDictionary }) {
  const { preview, technology } = l;
  const specs = [technology.model, technology.coverage, technology.attention, technology.reports];
  return (
    <section
      aria-labelledby="preview-heading"
      className="on-dark bg-primary py-20 text-primary-foreground lg:py-28"
    >
      <Container>
        <div className="reveal max-w-3xl">
          <h2 id="preview-heading" className="display-lg text-balance">
            {preview.heading}
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-secondary">{preview.intro}</p>
        </div>

        <div className="mt-12 lg:mt-14">
          <PreviewDemo preview={preview} illustrative={l.illustrative} />
          <p className="mt-4 text-sm text-secondary">{preview.note}</p>
        </div>

        <div id="technology" className="mt-16 scroll-mt-4 lg:mt-20">
          <h2 className="reveal font-heading text-h2">{technology.heading}</h2>
          <dl className="mt-6 grid gap-x-8 sm:grid-cols-2 lg:grid-cols-4">
            {specs.map(({ title, body }) => (
              <div key={title} className="reveal border-t border-[var(--hairline-dark)] py-5">
                <dt className="font-heading text-h3">{title}</dt>
                <dd className="mt-1.5 leading-relaxed text-secondary">{body}</dd>
              </div>
            ))}
          </dl>
        </div>
      </Container>
    </section>
  );
}
