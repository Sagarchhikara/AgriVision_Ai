import { AppShell } from "@/components/app-shell";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/dictionaries";

/** The shell of the diagnosis screens. The landing page in (marketing) brings its own. */
export default async function AppLayout({ children, params }: LayoutProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) return null; // [locale]/layout.tsx has already called notFound().
  const dictionary = await getDictionary(locale);

  return <AppShell skipToContent={dictionary.app.skipToContent}>{children}</AppShell>;
}
