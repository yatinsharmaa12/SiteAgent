import { request } from "./client";
import type { Company } from "../types";
export const listCompanies = () => request<Company[]>("/companies");
export const createCompany = (payload: { name: string; website_url: string }) => request<Company>("/companies", { method: "POST", body: JSON.stringify(payload) });
