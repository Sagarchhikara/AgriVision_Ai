import type { Metadata } from "next";

import { UploadScreen } from "@/components/upload/upload-screen";
import { isLocale } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/dictionaries";

export async function generateMetadata({
  params,
}: PageProps<"/[locale]/diagnose">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) return {};
  const t = await getDictionary(locale);
  return { title: t.upload.title };
}

export default function DiagnosePage() {
  return <UploadScreen />;
}
