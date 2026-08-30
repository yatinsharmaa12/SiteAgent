import { request } from "./client";
import type { ChatResponse } from "../types";
export const askCompany = (company_id: number, question: string) => request<ChatResponse>("/chat", { method: "POST", body: JSON.stringify({ company_id, question }) });
