export const guidance: Record<string, string> = {
  file_too_large: "Reduce the file size and try again.",
  pdf_required: "Choose a PDF file.",
  empty_or_scanned_page: "Choose a PDF with readable text on every page.",
  unreadable_pdf: "Choose a readable, uncorrupted PDF.",
  required_sections_missing: "Enter at least one report section and save again.",
  unauthorized: "Check your local demo token.",
  database_unavailable:
    "Database unavailable. Restore the database connection and retry.",
  source_not_ready_or_not_allowed:
    "Select only ready sources you are allowed to use.",
};

export async function apiRequest(token: string, path: string, options: RequestInit = {}) {
  const response = await fetch("/api/v1" + path, {
    ...options,
    headers: { Authorization: "Bearer " + token, ...options.headers },
  });
  const body = await response.json();
  if (!response.ok) {
    const code = body.error?.code || "request_failed";
    const fields = body.error?.fields as string[] | undefined;
    throw new Error((guidance[code] || code.replaceAll("_", " ")) +
      (fields?.length ? `: ${fields.join(", ")}` : ""));
  }
  return body;
}
