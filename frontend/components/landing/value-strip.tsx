import { BarChart3, FileText, Languages, ScanSearch } from "lucide-react";

import { Container } from "@/components/landing/shared";
import type { LandingDictionary } from "@/lib/i18n/landing/en";

export function ValueStrip({ value }: { value: LandingDictionary["value"] }) {
  const items = [
    { icon: ScanSearch, label: value.analysis },
    { icon: BarChart3, label: value.predictions },
    { icon: Languages, label: value.languages },
    { icon: FileText, label: value.reports },
  ];
  return (
    <section aria-labelledby="value-heading" className="on-dark bg-primary text-primary-foreground">
      <h2 id="value-heading" className="sr-only">
        {value.heading}
      </h2>
      <Container>
        <ul className="grid grid-cols-2 lg:grid-cols-4">
          {items.map(({ icon: Icon, label }) => (
            <li
              key={label}
              className="flex items-center gap-3 border-[var(--hairline-dark)] py-5 odd:border-r odd:pr-4 even:pl-4 max-lg:nth-[n+3]:border-t lg:border-r lg:px-6 lg:py-7 lg:first:pl-0 lg:last:border-r-0"
            >
              <Icon aria-hidden className="size-6 shrink-0 text-[var(--harvest)]" />
              <span className="text-sm font-medium sm:text-base">{label}</span>
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}
