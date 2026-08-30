import { request } from "./client";
export async function login(email: string, password: string) {
  const result = await request<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
  await chrome.storage.local.set({ fieldnote_token: result.access_token }); return result;
}
export function logout() { return chrome.storage.local.remove("fieldnote_token"); }
