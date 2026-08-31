chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
