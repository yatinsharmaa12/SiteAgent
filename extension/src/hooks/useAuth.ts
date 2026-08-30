import { useEffect, useState } from "react";
import { login, logout } from "../api/auth";

export function useAuth() {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => { chrome.storage.local.get("fieldnote_token").then(value => setToken(value.fieldnote_token ?? null)); }, []);
  return {
    token,
    signIn: async (email: string, password: string) => { const result = await login(email, password); setToken(result.access_token); },
    signOut: async () => { await logout(); setToken(null); },
  };
}
