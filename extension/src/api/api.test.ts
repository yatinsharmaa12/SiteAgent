import { beforeEach, describe, expect, it, vi } from "vitest";
import { login, logout } from "./auth";
import { askCompany, uniqueSources } from "./chat";
import { createCompany } from "./companies";
import { cancelCrawl, getCrawlJob, startCrawl } from "./crawl";
import { ApiError } from "./client";

const storage = new Map<string, unknown>();
beforeEach(() => { storage.clear(); vi.restoreAllMocks(); (globalThis as any).chrome = { storage: { local: { get: vi.fn(async (key: string) => ({ [key]: storage.get(key) })), set: vi.fn(async (value: Record<string, unknown>) => Object.entries(value).forEach(([key, value]) => storage.set(key, value))), remove: vi.fn(async (key: string) => storage.delete(key)) } } }; });

describe("extension API client", () => {
  it("stores login tokens and supports logout", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ access_token: "jwt" }), { status: 200 }));
    await login("user@example.com", "secret");
    expect(storage.get("fieldnote_token")).toBe("jwt");
    await logout();
    expect(storage.has("fieldnote_token")).toBe(false);
  });

  it("uses existing company, crawl, chat, and cancellation routes", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/companies")) return new Response(JSON.stringify([{ id: 3, name: "Acme", website_url: "https://acme.com" }]), { status: 200 });
      if (url.endsWith("/companies/3")) return new Response(JSON.stringify({ id: 3, name: "Acme", website_url: "https://acme.com" }), { status: 200 });
      if (url.endsWith("/crawl")) return new Response(JSON.stringify({ job_id: 8 }), { status: 200 });
      if (url.includes("crawl-jobs/8")) return new Response(JSON.stringify({ job_id: 8, status: "COMPLETED", company_id: 3 }), { status: 200 });
      return new Response(JSON.stringify({ answer: "Yes", sources: [{ title: "About", url: "https://acme.com/about" }] }), { status: 200 });
    });
    await createCompany({ name: "Acme", website_url: "https://acme.com" });
    await startCrawl(3); await getCrawlJob(3, 8); await cancelCrawl(3, 8); await askCompany(3, "What do you do?");
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });

  it("exposes safe 502 and 401 API errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: "The AI service is temporarily unavailable." }), { status: 502 }));
    await expect(askCompany(3, "Question")).rejects.toEqual(expect.objectContaining({ status: 502, message: expect.stringContaining("temporarily") } satisfies Partial<ApiError>));
  });

  it("removes duplicate source URLs while preserving order", () => {
    expect(uniqueSources([{ title: "Home", url: "https://acme.com" }, { title: "Home again", url: "https://acme.com" }, { title: "About", url: "https://acme.com/about" }])).toEqual([
      { title: "Home", url: "https://acme.com" }, { title: "About", url: "https://acme.com/about" },
    ]);
  });
});
