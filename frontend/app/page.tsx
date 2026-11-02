import { ConnectionCheck } from "@/components/connection-check";

// Phase 1 placeholder: confirms the frontend can reach the backend (base URL
// and CORS). Replaced by the upload screen in Phase 2.
export default function Home() {
  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="text-2xl font-semibold">AgriVision</h1>
      <ConnectionCheck />
    </main>
  );
}
