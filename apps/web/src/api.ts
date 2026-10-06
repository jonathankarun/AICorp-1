import type { AssignmentCreate, AssignmentResponse } from "./types";

// One configuration point for the API URL. Components never hard-code backend URLs.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type ApiFieldError = { field: string; message: string };

export class ApiValidationError extends Error {
  fields: ApiFieldError[];

  constructor(message: string, fields: ApiFieldError[]) {
    super(message);
    this.fields = fields;
  }
}

export async function createAssignment(
  payload: AssignmentCreate,
): Promise<AssignmentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/assignments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (response.status === 422) {
    const body = await response.json();
    throw new ApiValidationError(body.error.message, body.error.fields);
  }

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return response.json();
}

export async function checkHealth(): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`);
  if (!response.ok) return false;
  const body = await response.json();
  return body.status === "ok";
}
