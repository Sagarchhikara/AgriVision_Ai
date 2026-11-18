import { Plus } from "lucide-react";
import type { ReactNode } from "react";

import { Container } from "@/components/landing/shared";
import type { Locale } from "@/lib/i18n/config";
import type { Dictionary } from "@/lib/i18n/dictionaries/en";
import type { LandingDictionary } from "@/lib/i18n/landing/en";

function Item({ question, children }: { question: string; children: ReactNode }) {
  return (
    <details name="faq" className="faq-item border-b">
      <summary className="flex min-h-16 cursor-pointer items-center justify-between gap-4 rounded-lg py-4 font-heading text-h3">
        {question}
        <Plus aria-hidden className="faq-icon size-5 shrink-0 text-primary transition-[rotate]" />
      </summary>
      <div className="pb-5 leading-relaxed text-muted-foreground">{children}</div>
    </details>
  );
}

export function Faq({
  faq,
  t,
  locale,
}: {
  faq: LandingDictionary["faq"];
  t: Dictionary;
  locale: Locale;
}) {
  // From the class list, so this stays true if the model's crops change.
  const crops = [...new Set(Object.values(t.classes).map(({ crop }) => crop))];
  const cropList = new Intl.ListFormat(locale, { type: "conjunction" }).format(crops);

  return (
    <section id="faq" aria-labelledby="faq-heading" className="py-20 lg:py-28">
      <Container className="grid gap-8 lg:grid-cols-12 lg:gap-16">
        <h2 id="faq-heading" className="display-lg reveal text-balance lg:col-span-5">
          {faq.heading}
        </h2>
        <div className="reveal border-t lg:col-span-7">
          <Item question={faq.diagnosis.question}>{faq.diagnosis.answer}</Item>
          <Item question={faq.crops.question}>
            {faq.crops.answer} <span className="font-medium text-foreground">{cropList}</span>
          </Item>
          <Item question={faq.photos.question}>{faq.photos.answer}</Item>
          <Item question={faq.uncertain.question}>{faq.uncertain.answer}</Item>
          <Item question={faq.privacy.question}>{faq.privacy.answer}</Item>
          <Item question={faq.account.question}>{faq.account.answer}</Item>
        </div>
      </Container>
    </section>
  );
}
