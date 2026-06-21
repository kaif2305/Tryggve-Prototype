import type { ReportResponse } from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000");

export async function submitIncidentReport(
  text: string,
  image: File | null,
): Promise<ReportResponse> {
  const formData = new FormData();
  formData.append("text", text);

  if (image) {
    formData.append("image", image);
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/report`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep default detail when body is not JSON.
    }
    throw new Error(detail);
  }

  return (await response.json()) as ReportResponse;
}
