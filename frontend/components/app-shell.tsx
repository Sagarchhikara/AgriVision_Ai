import type { ComponentProps, ReactNode } from "react";

import { SiteHeader } from "@/components/site-header";
import { cn } from "cn";

export function AppShell({
  skipToContent,
  children,
}: {
  skipToContent: string;
  children: ReactNode;
}) {
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-30 focus:rounded-lg focus:bg-primary focus:px-4 focus:py-3 focus:text-primary-foreground"
      >
        {skipToContent}
      </a>
      <SiteHeader />
      <main
        id="main"
        tabIndex={-1}
        className="mx-auto w-full max-w-7xl px-4 pt-6 pb-12 outline-none md:px-6 md:pt-8 lg:px-8"
      >
        {children}
      </main>
    </>
  );
}

/** Keeps a single-column page at a readable width inside the full-width shell. */
export function ReadingColumn({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("mx-auto w-full max-w-xl", className)} {...props} />;
}
