import { describe, expect, it } from "vitest";
import { companyMatchesSite, getSupportedSite, normalizeHostname } from "./site";

describe("active site identity", () => {
  it("normalizes www, paths, case, and trailing dots to one hostname", () => {
    expect(getSupportedSite("https://www.Example.com/about")).toEqual({ url: "https://www.example.com/about", hostname: "example.com" });
    expect(normalizeHostname("WWW.Example.com.")).toBe("example.com");
    expect(companyMatchesSite({ website_url: "https://example.com" }, { hostname: "example.com" })).toBe(true);
  });

  it("rejects browser-internal and unsupported URLs", () => {
    expect(getSupportedSite("chrome://extensions")).toBeNull();
    expect(getSupportedSite("chrome-extension://abc/index.html")).toBeNull();
    expect(getSupportedSite("file:///tmp/site.html")).toBeNull();
    expect(getSupportedSite("about:blank")).toBeNull();
  });
});
