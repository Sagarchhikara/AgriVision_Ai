import type { Metadata, Viewport } from "next";

import { LocaleHtml } from "@/components/locale-html";
import { AnalysisProvider } from "@/state/analysis-context";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "AgriVision", template: "%s · AgriVision" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f9f7f0",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <LocaleHtml>
      <body className="min-h-dvh">
        <AnalysisProvider>{children}</AnalysisProvider>
      </body>
    </LocaleHtml>
  );
}
