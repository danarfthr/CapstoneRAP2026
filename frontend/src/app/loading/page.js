/**
 * Route "/loading" — [3] LOADING
 * Isi halaman ada di src/components/loading/LoadingScreen.js
 *
 * Catatan: folder ini bernama "loading" sebagai nama URL biasa, BUKAN file
 * khusus Next.js `loading.js`. LoadingScreen membaca query string
 * (useSearchParams), jadi wajib dibungkus <Suspense>.
 */
import { Suspense } from "react";
import LoadingScreen from "@/components/loading/LoadingScreen";

export const metadata = {
  title: "Preparing Analysis",
};

export default function LoadingPage() {
  return (
    <Suspense>
      <LoadingScreen />
    </Suspense>
  );
}
