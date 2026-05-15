import React, { useMemo, useState } from 'react';

const WORKFLOWS = [
  'Single match prediction',
  'Gameweek prediction batch',
  'Knockout prediction',
  'Finals special',
  'World Cup group or round prediction',
  'Fantasy quick picks',
];

function CopyButton({ text, children }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  };
  return (
    <button type="button" onClick={copy} className="rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] hover:border-[#58A6FF] hover:text-white">
      {copied ? 'Copied' : children}
    </button>
  );
}

export default function PredictionStudio() {
  const [workflow, setWorkflow] = useState(WORKFLOWS[0]);
  const modulePlan = useMemo(() => [
    'Own fixture and prediction schemas here, separate from cinematic scene prompts.',
    'Use low-animation data cards, comparison panels, and stat layouts.',
    'Keep predictions as entertainment and football discussion, not betting advice.',
    'Use manual-first data until approved providers are configured.',
    'Reuse shared metadata/export ideas only after manual review.',
  ], []);

  return (
    <div className="min-h-screen bg-[#010409] text-[#C9D1D9]">
      <div className="mx-auto max-w-6xl px-4 py-6 md:px-8">
        <header className="mb-6 border-b border-[#21262D] pb-5">
          <p className="text-xs font-bold uppercase tracking-wide text-[#58A6FF]">Separate Module</p>
          <h1 className="mt-2 text-2xl font-black text-white md:text-3xl">Football Prediction Studio</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#8B949E]">
            Data-card football predictions for fixtures, gameweeks, knockout paths, and finals. This stays separate from Sports Clip Lab cinematic workflows.
          </p>
        </header>

        <section className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <aside className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
            <label className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">Workflow</label>
            <select
              value={workflow}
              onChange={(event) => setWorkflow(event.target.value)}
              className="mt-2 w-full rounded-lg border border-[#30363D] bg-[#010409] px-3 py-2 text-sm text-white outline-none focus:border-[#58A6FF]"
            >
              {WORKFLOWS.map((item) => <option key={item}>{item}</option>)}
            </select>
            <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs leading-5 text-amber-200">
              No betting advice, no guaranteed outcomes, no paid data APIs, and no auto-posting.
            </div>
          </aside>

          <main className="space-y-4">
            <section className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-white">Module Plan</h2>
                  <p className="text-xs text-[#8B949E]">Prediction Studio owns data-card prediction workflows; Sports Clip Lab remains cinematic.</p>
                </div>
                <CopyButton text={modulePlan.join('\n')}>Copy Plan</CopyButton>
              </div>
              <ul className="space-y-2 text-sm leading-6">
                {modulePlan.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </section>

            <section className="grid gap-3 md:grid-cols-3">
              {['Fixtures', 'Prediction schema', 'Data cards'].map((label) => (
                <div key={label} className="rounded-lg border border-[#30363D] bg-[#010409] p-4">
                  <p className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">{label}</p>
                  <p className="mt-2 text-sm text-white">Owned by Prediction Studio.</p>
                </div>
              ))}
            </section>
          </main>
        </section>
      </div>
    </div>
  );
}
