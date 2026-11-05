"use client";

import { Compass } from "lucide-react";
import Link from "next/link";

import { useI18n } from "@/components/i18n-provider";
import { Button } from "@/components/ui/button";

export function NotFoundScreen() {
  const { t, href } = useI18n();
  return (
    <div className="flex flex-col items-center gap-4 py-12 text-center">
      <Compass aria-hidden className="size-12 text-muted-foreground" />
      <h1 className="text-2xl font-semibold">{t.notFound.title}</h1>
      <p className="text-muted-foreground">{t.notFound.body}</p>
      <Button asChild size="lg">
        <Link href={href("/")}>{t.notFound.action}</Link>
      </Button>
    </div>
  );
}
