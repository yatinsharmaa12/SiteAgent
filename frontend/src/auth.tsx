import { createContext, useContext, useState, type ReactNode } from "react";
import { api } from "./api";

type AuthContextValue = { token: string | null; login: (email: string, password: string) => Promise<void>; logout: () => void };
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(() => sessionStorage.getItem("fieldnote_token"));
  async function login(email: string, password: string) {
    const result = await api.login(email, password);
    sessionStorage.setItem("fieldnote_token", result.access_token);
    setToken(result.access_token);
  }
  function logout() { sessionStorage.removeItem("fieldnote_token"); setToken(null); }
  return <AuthContext.Provider value={{ token, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
