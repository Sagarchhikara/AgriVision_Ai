"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { Dialog } from "radix-ui";
import { useRef, useState, useSyncExternalStore, type MouseEvent } from "react";

import { useI18n } from "@/components/i18n-provider";
import { LanguageSwitcher } from "@/components/language-switcher";
import { Container } from "@/components/landing/shared";
import { Button } from "@/components/ui/button";
import { Wordmark } from "@/components/wordmark";
import { DIAGNOSE_PATH } from "@/lib/i18n/config";
import type { LandingDictionary } from "@/lib/i18n/landing/en";
import { cn } from "cn";

function subscribeToScroll(onChange: () => void) {
  window.addEventListener("scroll", onChange, { passive: true });
  return () => window.removeEventListener("scroll", onChange);
}

export function LandingNav({ nav }: { nav: LandingDictionary["nav"] }) {
  const { t, href } = useI18n();
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const pendingAnchor = useRef<string | null>(null);
  const scrolled = useSyncExternalStore(
    subscribeToScroll,
    () => window.scrollY > 8,
    () => false,
  );

  // The drawer's anchors wait for it to close: Radix locks scrolling while it is
  // open, then returns focus to the trigger, and the browser scrolls to reveal
  // that sticky button, undoing a jump made any earlier.
  const goToAnchor = (event: MouseEvent, id: string) => {
    event.preventDefault();
    pendingAnchor.current = id;
    setOpen(false);
  };
  const afterClose = (event: Event) => {
    event.preventDefault();
    const id = pendingAnchor.current;
    pendingAnchor.current = null;
    if (!id) trigger.current?.focus({ preventScroll: true });
    else if (window.location.hash === `#${id}`) document.getElementById(id)?.scrollIntoView();
    // A same-page fragment, not a route. Native navigation also moves the keyboard
    // start point to the section, which router.push does not.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    else window.location.assign(`#${id}`);
  };

  const links = [
    { id: "how-it-works", label: nav.howItWorks },
    { id: "features", label: nav.features },
    { id: "technology", label: nav.technology },
    { id: "faq", label: nav.faq },
  ];

  return (
    <header
      className={cn(
        "sticky top-0 z-30 border-b transition-[background-color,border-color,box-shadow] print:static",
        scrolled
          ? "border-border bg-background/95 shadow-card"
          : "border-transparent bg-background",
      )}
    >
      <Container className="flex h-16 items-center justify-between gap-3 lg:h-[4.5rem]">
        <Link
          href={href("/")}
          aria-label={t.app.homeLink}
          className="-mx-1 flex min-h-11 items-center rounded-lg px-1"
        >
          <Wordmark name={t.app.name} />
        </Link>

        <nav aria-label={nav.label} className="hidden lg:block">
          <ul className="flex items-center gap-1">
            {links.map(({ id, label }) => (
              <li key={id}>
                <a
                  href={`#${id}`}
                  className="flex min-h-11 items-center rounded-lg px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center gap-2">
          <div className="hidden md:block">
            <LanguageSwitcher />
          </div>
          <Button asChild size="sm" className="hidden sm:inline-flex">
            <Link href={href(DIAGNOSE_PATH)}>{nav.cta}</Link>
          </Button>

          <Dialog.Root open={open} onOpenChange={setOpen}>
            <Dialog.Trigger asChild>
              <Button
                ref={trigger}
                variant="ghost"
                size="sm"
                aria-label={nav.openMenu}
                className="w-11 px-0 lg:hidden"
              >
                <Menu aria-hidden />
              </Button>
            </Dialog.Trigger>
            {/* No portal: the panel stays inside .landing, whose colours it uses. */}
            <Dialog.Overlay className="fixed inset-0 z-40 bg-foreground/40 data-open:animate-in data-open:fade-in-0 data-closed:animate-out data-closed:fade-out-0 motion-reduce:animate-none" />
            <Dialog.Content
              onCloseAutoFocus={afterClose}
              className="fixed inset-y-0 right-0 z-50 flex w-[min(22rem,88vw)] flex-col gap-6 overflow-y-auto bg-background p-5 shadow-xl duration-200 data-open:animate-in data-open:slide-in-from-right data-closed:animate-out data-closed:slide-out-to-right motion-reduce:animate-none"
            >
              <div className="flex items-center justify-between">
                <Dialog.Title className="font-heading text-h3">{nav.menuTitle}</Dialog.Title>
                <Dialog.Close asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label={nav.closeMenu}
                    className="w-11 px-0"
                  >
                    <X aria-hidden />
                  </Button>
                </Dialog.Close>
              </div>
              <Dialog.Description className="sr-only">{nav.label}</Dialog.Description>
              <nav aria-label={nav.label}>
                <ul className="flex flex-col">
                  {links.map(({ id, label }) => (
                    <li key={id} className="border-b">
                      <a
                        href={`#${id}`}
                        onClick={(event) => goToAnchor(event, id)}
                        className="flex min-h-14 items-center text-lg font-semibold"
                      >
                        {label}
                      </a>
                    </li>
                  ))}
                </ul>
              </nav>
              <LanguageSwitcher />
              <Button asChild size="lg" className="mt-auto">
                <Link href={href(DIAGNOSE_PATH)}>{nav.cta}</Link>
              </Button>
            </Dialog.Content>
          </Dialog.Root>
        </div>
      </Container>
    </header>
  );
}
