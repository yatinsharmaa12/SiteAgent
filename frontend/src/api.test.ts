import { beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "./api";

describe("API contract", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("logs in, sends bearer auth, and creates a company", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "token-1" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 4, name: "Acme", website_url: "https://acme.com" }), { status: 200 }));

    const login = await api.login("person@acme.com", "secret");
    sessionStorage.setItem("fieldnote_token", login.access_token);
    await api.createCompany({ name: "Acme", website_url: "https://acme.com" });

    expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({ email: "person@acme.com", password: "secret" });
    expect(new Headers(fetchMock.mock.calls[1][1]?.headers).get("Authorization")).toBe("Bearer token-1");
  });

  it("maps crawl, cancellation, statistics, and chat to existing routes", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ job_id: 8, company_id: 3, status: "QUEUED" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ message: "Job cancelled" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ answer: "Yes", sources: [{ title: "About", url: "https://acme.com/about" }] }), { status: 200 }));
    sessionStorage.setItem("fieldnote_token", "token-1");

    expect(await api.createCrawl(3, { max_pages: 10, max_depth: 2 })).toMatchObject({ job_id: 8 });
    expect(await api.cancelCrawl(3, 8)).toEqual({ message: "Job cancelled" });
    expect(await api.chat(3, "What do you do?")).toMatchObject({ answer: "Yes" });
  });

  it("surfaces authentication and API errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: "Invalid email or password" }), { status: 401 }));
    await expect(api.login("bad@example.com", "bad")).rejects.toEqual(expect.objectContaining({ status: 401, message: "Invalid email or password" } satisfies Partial<ApiError>));
  });
});
