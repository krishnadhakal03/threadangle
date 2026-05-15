import React, { useMemo, useState } from 'react';

export default function WorkflowQAPanel({ title, items }) {
  const [checked, setChecked] = useState({});
  const completed = useMemo(
    () => items.filter((item) => checked[item.id]).length,
    [checked, items],
  );
  const report = useMemo(
    () => items.map((item) => `${checked[item.id] ? '[x]' : '[ ]'} ${item.label}`).join('\n'),
    [checked, items],
  );

  const copyReport = async () => {
    try {
      await navigator.clipboard.writeText(`${title}\n${report}`);
    } catch {
      // Clipboard is optional for local QA.
    }
  };

  return (
    <section className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
      <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">{title}</h2>
          <p className="text-xs text-[#8B949E]">{completed}/{items.length} checks completed. Local manual QA only.</p>
        </div>
        <button
          type="button"
          onClick={copyReport}
          className="inline-flex items-center justify-center rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] hover:border-[#58A6FF] hover:text-white"
        >
          Copy QA Report
        </button>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        {items.map((item) => (
          <label key={item.id} className="flex items-start gap-2 rounded-lg border border-[#30363D] bg-[#010409] p-3 text-sm leading-5 text-[#C9D1D9]">
            <input
              type="checkbox"
              checked={Boolean(checked[item.id])}
              onChange={(event) => setChecked((current) => ({ ...current, [item.id]: event.target.checked }))}
              className="mt-1"
            />
            <span>{item.label}</span>
          </label>
        ))}
      </div>
    </section>
  );
}
