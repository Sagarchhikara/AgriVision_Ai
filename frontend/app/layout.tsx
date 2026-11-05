import type { Metadata, Viewport } from "next";

import { I18nProvider } from "@/components/i18n-provider";
import { SiteHeader } from "@/components/site-header";
import { DEFAULT_LOCALE } from "@/lib/i18n/config";
import { AnalysisProvider } from "@/state/analysis-context";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "AgriVision", template: "%s · AgriVision" },
  description: "Check a crop leaf photo for signs of disease.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f9f7f0",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang={DEFAULT_LOCALE}>
      <body className="min-h-dvh">
        <I18nProvider locale={DEFAULT_LOCALE}>
          <AnalysisProvider>
            <SiteHeader />
            <main className="mx-auto w-full max-w-xl px-4 pt-6 pb-12">{children}</main>
          </AnalysisProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
