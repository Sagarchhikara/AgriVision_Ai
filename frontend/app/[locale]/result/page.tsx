import type { Metadata } from "next";

import { ResultScreen } from "@/components/result/result-screen";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/dictionaries";

export async function generateMetadata({
  params,
}: PageProps<"/[locale]/result">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  const t = await getDictionary(locale);
  return { title: t.result.pageTitle };
}

export default function ResultPage() {
  return <ResultScreen />;
}
