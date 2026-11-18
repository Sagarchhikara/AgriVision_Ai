import { Camera, MessageCircleQuestion, Sparkles, TriangleAlert } from "lucide-react";

import { Container } from "@/components/landing/shared";
import type { LandingDictionary } from "@/lib/i18n/landing/en";

export function ResponsibleAi({ responsible }: { responsible: LandingDictionary["responsible"] }) {
  const items = [
    { icon: Sparkles, ...responsible.suggestion },
    { icon: TriangleAlert, ...responsible.accuracy },
    { icon: Camera, ...responsible.conditions },
    { icon: MessageCircleQuestion, ...responsible.expert },
  ];
  return (
    <section aria-labelledby="responsible-heading" className="bg-secondary py-20 lg:py-28">
      <Container className="grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="reveal lg:col-span-5">
          <h2 id="responsible-heading" className="display-lg text-balance">
            {responsible.heading}
          </h2>
          <p className="mt-5 text-lg leading-relaxed text-muted-foreground">{responsible.body}</p>
        </div>
        <ul className="flex flex-col lg:col-span-7">
          {items.map(({ icon: Icon, title, body }) => (
            <li
              key={title}
              className="reveal flex gap-4 border-t border-foreground/15 py-6 first:border-t-0 first:pt-0"
            >
              <Icon aria-hidden className="mt-0.5 size-6 shrink-0 text-primary" />
              <div>
                <h3 className="font-heading text-xl font-bold">{title}</h3>
                <p className="mt-1 leading-relaxed text-foreground/80">{body}</p>
              </div>
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}
