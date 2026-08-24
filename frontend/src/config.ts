const rawApiUrl = import.meta.env.VITE_API_URL?.trim();
const demoLoginOverride = import.meta.env.VITE_ENABLE_DEMO_LOGIN;
const fallbackApiUrl = import.meta.env.DEV ? "http://localhost:8000/api/v1" : "";

if (!rawApiUrl && !fallbackApiUrl) {
  throw new Error("VITE_API_URL must be set for production deployments.");
}

export const API_URL = (rawApiUrl || fallbackApiUrl).replace(/\/+$/, "");
export const DEMO_LOGIN_ENABLED = demoLoginOverride
  ? demoLoginOverride === "true"
  : import.meta.env.DEV;
