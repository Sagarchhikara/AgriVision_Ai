import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "cn";
import { Slot } from "radix-ui";

const cardVariants = cva("rounded-xl", {
  variants: {
    variant: {
      default: "border bg-card text-card-foreground shadow-card",
      muted: "border bg-muted/40",
      soft: "bg-secondary/60",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

function Card({
  className,
  variant,
  asChild = false,
  ...props
}: React.ComponentProps<"div"> &
  VariantProps<typeof cardVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot.Root : "div";
  return <Comp data-slot="card" className={cn(cardVariants({ variant }), className)} {...props} />;
}

export { Card };
