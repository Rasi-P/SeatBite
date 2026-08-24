import { API_URL } from "../config";

type ApiOptions = RequestInit & { customer?: boolean };

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(status: number, details: unknown) {
    super(typeof details === "string" ? details : "Request failed");
    this.status = status;
    this.details = details;
  }
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  const access = localStorage.getItem("seatbite_access");
  const customerToken = localStorage.getItem("seatbite_session");
  if (access && !options.customer) headers.set("Authorization", `Bearer ${access}`);
  if (customerToken && options.customer) headers.set("X-Session-Token", customerToken);
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let payload: unknown;
    try { payload = await response.json(); } catch { payload = response.statusText; }
    throw new ApiError(response.status, payload);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function apiList<T>(path: string, options: ApiOptions = {}): Promise<T[]> {
  const data = await apiFetch<T[] | { results: T[] }>(path, options);
  return Array.isArray(data) ? data : data.results;
}

export const money = (value: string | number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(Number(value));
