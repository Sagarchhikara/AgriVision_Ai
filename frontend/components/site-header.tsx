"use client";

import { Sprout } from "lucide-react";
import Link from "next/link";

import { useI18n } from "@/components/i18n-provider";

export function SiteHeader() {
  const { t } = useI18n();
  return (
    <header className="border-b border-border/70 bg-card/60">
      <div className="mx-auto flex h-14 max-w-xl items-center px-4">
        <Link
          href="/"
          aria-label={t.app.homeLink}
          className="-mx-2 flex min-h-11 items-center gap-2 rounded-lg px-2 text-lg font-semibold text-primary focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          <Sprout aria-hidden className="size-6" />
          {t.app.name}
        </Link>
      </div>
    </header>
  );
}
