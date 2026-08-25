const rawApiUrl = import.meta.env.VITE_API_URL?.trim();
const fallbackApiUrl = import.meta.env.DEV ? "http://localhost:8000/api/v1" : "";

if (!rawApiUrl && !fallbackApiUrl) {
  throw new Error("VITE_API_URL must be set for production deployments.");
}

export const API_URL = (rawApiUrl || fallbackApiUrl).replace(/\/+$/, "");
