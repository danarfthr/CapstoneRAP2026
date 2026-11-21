import { proxyToBackend } from "@/lib/backend";

export async function GET(request) {
  return proxyToBackend(request, "/api/dataset");
}
