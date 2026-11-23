import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
const FILTER_KEYS = ["types", "platforms", "range", "from", "to"];

export async function proxyToBackend(request, path) {
  const incoming = request.nextUrl.searchParams;
  const params = new URLSearchParams();
  FILTER_KEYS.forEach((key) => {
    const value = incoming.get(key);
    if (value) params.set(key, value);
  });

  try {
    const response = await fetch(`${BACKEND_URL}${path}?${params}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Backend responded with status ${response.status}`);
    return NextResponse.json(await response.json(), { status: 200 });
  } catch (error) {
    console.error(`Failed to fetch ${path} from backend:`, error);
    return NextResponse.json({ error: `Failed to fetch ${path}` }, { status: 502 });
  }
}
