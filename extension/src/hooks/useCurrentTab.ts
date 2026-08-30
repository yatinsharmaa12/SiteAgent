import { useEffect, useState } from "react";
import { getSupportedSite } from "../utils/site";

export function useCurrentTab() {
  const [site, setSite] = useState<ReturnType<typeof getSupportedSite> | undefined>();
  useEffect(() => { chrome.tabs.query({ active: true, currentWindow: true }).then(tabs => setSite(getSupportedSite(tabs[0]?.url))); }, []);
  return site;
}
