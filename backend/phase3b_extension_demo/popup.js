const button = document.getElementById("summarize");
const result = document.getElementById("result");

function summarizeText(text) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  if (!clean) {
    return "No readable page text found.";
  }

  const sentences = clean.match(/[^.!?]+[.!?]+/g) || [clean];
  const summary = sentences.slice(0, 3).join(" ").trim();
  const wordCount = clean.split(/\s+/).filter(Boolean).length;
  return `Summary:\n${summary}\n\nEstimated length: ${wordCount} words`;
}

button.addEventListener("click", async () => {
  result.textContent = "Reading page...";
  const tabs = await chrome.tabs.query({ currentWindow: true });
  const tab = tabs.find((item) => item.url && /^https?:\/\//.test(item.url));
  if (!tab || !tab.id) {
    result.textContent = "No active tab found.";
    return;
  }

  const [injection] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.body.innerText,
  });

  result.textContent = summarizeText(injection && injection.result);
});
