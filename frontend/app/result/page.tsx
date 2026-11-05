import type { Metadata } from "next";

import { ResultScreen } from "@/components/result/result-screen";

export const metadata: Metadata = { title: "Result" };

export default function ResultPage() {
  return <ResultScreen />;
}
