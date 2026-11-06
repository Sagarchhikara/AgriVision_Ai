import * as React from "react";
import { cn } from "cn";

/** Native on purpose: it opens the phone's own picker and costs no JavaScript. */
function NativeSelect({ className, ...props }: React.ComponentProps<"select">) {
  return (
    <select
      data-slot="native-select"
      className={cn(
        "min-h-12 w-full rounded-lg border border-input bg-card px-3 text-base disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export { NativeSelect };
