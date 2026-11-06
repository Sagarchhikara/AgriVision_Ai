import { notFound } from "next/navigation";

// Unmatched paths would otherwise skip [locale]/not-found.tsx, and with it the
// translated page and the site header.
export default function CatchAll() {
  notFound();
}
