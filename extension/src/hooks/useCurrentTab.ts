import { useEffect, useState } from "react";
import { getSupportedSite } from "../utils/site";

export function useCurrentTab() {
  const [site, setSite] = useState<ReturnType<typeof getSupportedSite> | undefined>();
  useEffect(() => {
    let active = true;
    const update = () => chrome.tabs.query({ active: true, currentWindow: true }).then(tabs => {
      if (active) setSite(getSupportedSite(tabs[0]?.url));
    });
    update();
    const onActivated = () => update();
    const onUpdated = (_tabId: number, changeInfo: chrome.tabs.TabChangeInfo, tab: chrome.tabs.Tab) => {
      if (tab.active && changeInfo.url) update();
    };
    chrome.tabs.onActivated.addListener(onActivated);
    chrome.tabs.onUpdated.addListener(onUpdated);
    return () => { active = false; chrome.tabs.onActivated.removeListener(onActivated); chrome.tabs.onUpdated.removeListener(onUpdated); };
  }, []);
  return site;
}
