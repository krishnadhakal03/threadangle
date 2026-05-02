// Prevent global/workspace shortcuts from stealing normal typing keys inside text fields.
//
// Video Studio uses drag/reorder and modal keyboard handling. During manual QA,
// the Space key was intercepted before Hook/Body/CTA inputs could type normal
// sentences. This capture-phase guard keeps text editing events inside form
// controls and contenteditable regions.

const TEXT_ENTRY_TAGS = new Set(['INPUT', 'TEXTAREA', 'SELECT']);

function isTextEntryTarget(target) {
  if (!target) return false;
  const element = target instanceof Element ? target : target?.parentElement;
  if (!element) return false;
  if (element.isContentEditable) return true;
  const closestEditable = element.closest?.('[contenteditable="true"], input, textarea, select');
  if (!closestEditable) return false;
  if (closestEditable.isContentEditable) return true;
  return TEXT_ENTRY_TAGS.has(closestEditable.tagName);
}

function preserveTextInputKeys(event) {
  if (!isTextEntryTarget(event.target)) return;

  const key = event.key || '';
  const code = event.code || '';

  // Do not interfere with browser/system shortcuts such as Ctrl+S, Ctrl+Z,
  // Cmd+A, Alt+Tab, etc. We only protect plain text-entry keys that global
  // app shortcuts commonly intercept.
  if (event.ctrlKey || event.metaKey || event.altKey) return;

  const isPlainTextEntryKey =
    key === ' ' ||
    code === 'Space' ||
    key === 'Enter' ||
    key === 'Backspace' ||
    key === 'Delete' ||
    key === 'Tab' ||
    key.length === 1;

  if (!isPlainTextEntryKey) return;

  // Let the input itself receive and process the event, but stop parent/global
  // shortcut handlers from preventing default later in the event chain.
  event.stopPropagation();
}

if (typeof window !== 'undefined' && !window.__THREADANGLE_TEXT_INPUT_KEY_GUARD__) {
  window.__THREADANGLE_TEXT_INPUT_KEY_GUARD__ = true;
  window.addEventListener('keydown', preserveTextInputKeys, true);
  window.addEventListener('keypress', preserveTextInputKeys, true);
  window.addEventListener('keyup', preserveTextInputKeys, true);
}

export { preserveTextInputKeys };
