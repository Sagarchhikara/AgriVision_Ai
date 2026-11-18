import { Sprout } from "lucide-react";

export function Wordmark({ name }: { name: string }) {
  return (
    <span className="flex items-center gap-2.5">
      <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground">
        <Sprout aria-hidden className="size-5" />
      </span>
      {/* The language switcher needs the room on the narrowest phones. */}
      <span className="flex items-baseline gap-0.5 font-heading text-xl font-bold text-primary max-[345px]:sr-only">
        {name}
        <span aria-hidden className="size-1.5 rounded-full bg-highlight" />
      </span>
    </span>
  );
}
