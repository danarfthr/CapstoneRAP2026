/**
 * Route "/dashboard" — [4] DASHBOARD
 * Isi halaman ada di src/components/dashboard/DashboardPage.js
 *
 * DashboardPage membaca filter dari query string (useSearchParams),
 * jadi wajib dibungkus <Suspense>.
 */
import { Suspense } from "react";
import DashboardPage from "@/components/dashboard/DashboardPage";

export const metadata = {
  title: "Dashboard PLTU vs PLTN",
  description:
    "Dashboard analisis sentimen dan stance publik terhadap PLTU dan PLTN di Indonesia.",
};

export default function DashboardRoute() {
  return (
    <Suspense>
      <DashboardPage />
    </Suspense>
  );
}
