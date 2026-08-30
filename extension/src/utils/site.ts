export function normalizeHostname(value: string) {
  return value.toLowerCase().replace(/^www\./, "").replace(/\.$/, "");
}

export function getSupportedSite(url?: string): { url: string; hostname: string } | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    if (!["http:", "https:"].includes(parsed.protocol) || !parsed.hostname) return null;
    return { url: parsed.href, hostname: normalizeHostname(parsed.hostname) };
  } catch { return null; }
}

export function companyMatchesSite(company: { website_url: string }, site: { hostname: string }) {
  const companySite = getSupportedSite(company.website_url);
  return companySite?.hostname === site.hostname;
}
