import { z } from "zod";

const BASE = "";

export async function apiFetch<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  const json = await res.json();
  return schema.parse(json);
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  schema: z.ZodType<T>,
): Promise<T> {
  return apiFetch(path, schema, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
