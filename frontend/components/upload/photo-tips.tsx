"use client";

import { Crosshair, Focus, Leaf, type LucideIcon, Square, Sun, ZoomIn } from "lucide-react";

import { useI18n } from "@/components/i18n-provider";
import { Card } from "@/components/ui/card";
import type { Dictionary } from "@/lib/i18n/dictionaries/en";

const TIPS: { key: Exclude<keyof Dictionary["tips"], "title">; icon: LucideIcon }[] = [
  { key: "singleLeaf", icon: Leaf },
  { key: "closeUp", icon: ZoomIn },
  { key: "daylight", icon: Sun },
  { key: "plainBackground", icon: Square },
  { key: "inFocus", icon: Focus },
  { key: "centered", icon: Crosshair },
];

export function PhotoTips() {
  const { t } = useI18n();
  return (
    <Card asChild variant="soft" className="p-4">
      <section aria-labelledby="photo-tips-title">
        <h2 id="photo-tips-title" className="text-h3 text-secondary-foreground">
          {t.tips.title}
        </h2>
        <ul className="mt-3 grid grid-cols-1 gap-x-4 gap-y-2.5 min-[420px]:grid-cols-2">
          {TIPS.map(({ key, icon: Icon }) => (
            <li key={key} className="flex items-center gap-2.5">
              <span className="grid size-8 shrink-0 place-items-center rounded-full bg-card text-primary">
                <Icon aria-hidden className="size-4.5" />
              </span>
              <span className="text-sm leading-snug">{t.tips[key]}</span>
            </li>
          ))}
        </ul>
      </section>
    </Card>
  );
}
