/**
 * Route "/data" — [5] DATA VIEW (dibuka dari tombol "View Data" di dashboard)
 * Isi halaman ada di src/components/dataview/DataViewPage.js
 *
 * DataViewPage membaca filter dari query string (useSearchParams),
 * jadi wajib dibungkus <Suspense>.
 */
import { Suspense } from "react";
import DataViewPage from "@/components/dataview/DataViewPage";

export const metadata = {
  title: "Public Dataset & Annotations",
  description:
    "Data komentar YouTube dan berita beserta anotasi stance dan sentimen untuk PLTU dan PLTN.",
};

export default function DataRoute() {
  return (
    <Suspense>
      <DataViewPage />
    </Suspense>
  );
}
