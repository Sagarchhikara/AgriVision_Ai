import type { Metadata, Viewport } from "next";
import { Inter, Manrope } from "next/font/google";

import { LocaleHtml } from "@/components/locale-html";
import { AnalysisProvider } from "@/state/analysis-context";

import "./globals.css";

// Neither covers Devanagari or Gurmukhi: Hindi and Punjabi fall through to the
// Noto and system fonts in --font-sans.
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope", display: "swap" });

export const metadata: Metadata = {
  title: { default: "AgriVision", template: "%s · AgriVision" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f7f4ec",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <LocaleHtml className={`${inter.variable} ${manrope.variable}`}>
      <body className="min-h-dvh">
        <AnalysisProvider>{children}</AnalysisProvider>
      </body>
    </LocaleHtml>
  );
}
