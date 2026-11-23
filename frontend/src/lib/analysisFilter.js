/**
 * analysisFilter.js — Satu sumber kebenaran untuk filter analisis.
 *
 * Filter dipilih user di POP-UP, lalu dibawa lewat URL query string:
 *   /loading?types=PLTU,PLTN&platforms=youtube,news&range=all
 *   → /dashboard?types=PLTU,PLTN&platforms=youtube,news&range=all
 *
 * Dengan begini halaman loading & dashboard tetap tahu pilihan user,
 * dan URL dashboard bisa di-refresh/dibagikan tanpa kehilangan filter.
 */

/** Pilihan jenis pembangkit (key = nilai di URL & key data dari API). */
export const PLANT_TYPES = [
  { value: "pltu", label: "PLTU" },
  { value: "pltn", label: "PLTN" },
];

/** Pilihan sumber data. */
export const PLATFORMS = [
  { value: "youtube", label: "Youtube" },
  { value: "news", label: "News" },
];

/** Pilihan cepat rentang waktu. */
export const TIME_RANGES = [
  { value: "3m", label: "Last 3 Months" },
  { value: "6m", label: "Last 6 Months" },
  { value: "all", label: "All Time" },
];

/**
 * Nilai awal pop-up. Pop-up mewajibkan minimal satu PLTU/PLTN dipilih;
 * platforms kosong berarti "semua platform".
 */
export const DEFAULT_FILTER = {
  types: [],
  platforms: [],
  range: "all",
  from: "",
  to: "",
};

/**
 * Ubah objek filter → query string (tanpa "?").
 * Field kosong tidak ikut ditulis supaya URL tetap pendek.
 */
export function filterToQuery(filter) {
  const params = new URLSearchParams();

  if (filter.types.length) params.set("types", filter.types.join(","));
  if (filter.platforms.length) params.set("platforms", filter.platforms.join(","));

  if (filter.from || filter.to) {
    if (filter.from) params.set("from", filter.from);
    if (filter.to) params.set("to", filter.to);
  } else if (filter.range) {
    params.set("range", filter.range);
  }

  return params.toString();
}

/**
 * Ubah URLSearchParams → objek filter.
 * Nilai yang tidak dikenal dibuang; kalau types/platforms kosong,
 * dianggap memilih semua.
 */
export function queryToFilter(searchParams) {
  const readList = (key, options) => {
    const allowed = options.map((option) => option.value);
    const values = (searchParams.get(key) || "")
      .toLowerCase()
      .split(",")
      .filter((value) => allowed.includes(value));
    return values.length ? values : allowed;
  };

  return {
    types: readList("types", PLANT_TYPES),
    platforms: readList("platforms", PLATFORMS),
    range: searchParams.get("range") || "",
    from: searchParams.get("from") || "",
    to: searchParams.get("to") || "",
  };
}
