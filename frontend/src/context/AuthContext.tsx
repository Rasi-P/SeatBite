import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiFetch } from "../services/api";
import type { User } from "../types";

interface AuthValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("seatbite_access")) {
      setLoading(false);
      return;
    }
    apiFetch<User>("/auth/me/").then(setUser).catch(() => {
      localStorage.removeItem("seatbite_access");
      localStorage.removeItem("seatbite_refresh");
    }).finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const tokens = await apiFetch<{ access: string; refresh: string }>("/auth/token/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    localStorage.setItem("seatbite_access", tokens.access);
    localStorage.setItem("seatbite_refresh", tokens.refresh);
    const profile = await apiFetch<User>("/auth/me/");
    setUser(profile);
    return profile;
  };

  const logout = () => {
    localStorage.removeItem("seatbite_access");
    localStorage.removeItem("seatbite_refresh");
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}

