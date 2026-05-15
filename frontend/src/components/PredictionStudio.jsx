import React, { useMemo, useState } from 'react';
import WorkflowQAPanel from './WorkflowQAPanel';

const WORKFLOWS = [
  'Single match prediction',
  'Gameweek prediction batch',
  'Knockout prediction',
  'Finals special',
  'World Cup group or round prediction',
  'Fantasy quick picks',
];
const INITIAL_MATCH = {
  teamA: 'Arsenal',
  teamB: 'Manchester City',
  competition: 'Premier League',
  matchDate: '',
  tone: 'analytical',
  platform: 'All',
  recentFormA: 'W-W-D-W-L',
  recentFormB: 'W-W-W-D-W',
  injuriesNews: 'Manual notes only; verify before export.',
  headToHead: 'Recent meetings are tight, but pressure changes the matchup.',
  keyPlayers: 'Saka, Odegaard, Haaland, Foden',
  context: 'Title race pressure, home advantage, fixture congestion.',
};
const MATCH_SCENARIOS = {
  chelseaCity: {
    label: 'Chelsea vs Man City FA Cup',
    data: {
      teamA: 'Chelsea',
      teamB: 'Manchester City',
      competition: 'FA Cup',
      matchDate: '',
      tone: 'analytical',
      platform: 'All',
      recentFormA: 'W-D-W-L-W',
      recentFormB: 'W-W-D-W-W',
      injuriesNews: 'Manual team news check required before export.',
      headToHead: 'City bring control, Chelsea bring transition threat and cup-final chaos.',
      keyPlayers: 'Cole Palmer, Enzo Fernandez, Erling Haaland, Phil Foden',
      context: 'Cup pressure, midfield control, transition chances, late-game depth.',
    },
  },
  worldCup: {
    label: 'World Cup knockout',
    data: {
      teamA: 'Argentina',
      teamB: 'France',
      competition: 'World Cup Knockout',
      matchDate: '',
      tone: 'analytical',
      platform: 'All',
      recentFormA: 'W-W-D-W-W',
      recentFormB: 'W-D-W-W-L',
      injuriesNews: 'Manual squad/news verification required.',
      headToHead: 'Knockout games turn form into pressure, and one moment can flip the tie.',
      keyPlayers: 'Playmaker, striker, goalkeeper, pace winger',
      context: 'Knockout pressure, extra time risk, penalty pressure, national stakes.',
    },
  },
};
const GAMEWEEK_SAMPLE = [
  'Arsenal 2-1 Newcastle',
  'Chelsea 1-2 Manchester City',
  'Liverpool 3-1 Tottenham',
  'Aston Villa 1-1 Manchester United',
  'West Ham 0-2 Brighton',
];
const PREDICTION_QA_ITEMS = [
  { id: 'single-match', label: 'Single match inputs generate hook, analysis, metadata, prediction package, and data cards.' },
  { id: 'gameweek-route', label: 'Gameweek workflow remains inside Prediction Studio and does not alter Sports Clip Lab cinematic flow.' },
  { id: 'copy-export', label: 'Copy package, copy cards, and copy QA report actions work.' },
  { id: 'metadata', label: 'Prediction metadata includes title, caption, hashtags, CTA, and disclaimer.' },
  { id: 'data-cards', label: 'Preview cards are readable in 9:16 layout on desktop and narrow widths.' },
  { id: 'guardrails', label: 'No betting advice, no guaranteed outcomes, no paid APIs, and no auto-posting.' },
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
    <button type="button" onClick={copy} className="inline-flex min-h-9 max-w-full items-center justify-center rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-center text-xs font-semibold text-[#C9D1D9] hover:border-[#58A6FF] hover:text-white">
      {copied ? 'Copied' : children}
    </button>
  );
}

export default function PredictionStudio() {
  const [workflow, setWorkflow] = useState(WORKFLOWS[0]);
  const [matchForm, setMatchForm] = useState(INITIAL_MATCH);
  const updateMatch = (key, value) => setMatchForm((current) => ({ ...current, [key]: value }));
  const predictionPackage = useMemo(() => {
    const predictedScore = `${matchForm.teamA} 2-2 ${matchForm.teamB}`;
    return {
      hook: `${matchForm.teamA} vs ${matchForm.teamB}: who wins?`,
      formSummary: `${matchForm.teamA}: ${matchForm.recentFormA} | ${matchForm.teamB}: ${matchForm.recentFormB}`,
      headToHead: matchForm.headToHead,
      keyPlayers: matchForm.keyPlayers.split(',').map((item) => item.trim()).filter(Boolean),
      pressureFactors: matchForm.context.split(',').map((item) => item.trim()).filter(Boolean),
      predictedScore,
      confidence: 'medium',
      cta: 'Drop your score prediction. Agree or disagree?',
      disclaimer: 'Prediction is for entertainment and football discussion only, not betting advice.',
      metadata: {
        title: `${matchForm.teamA} vs ${matchForm.teamB} Prediction`,
        caption: `${matchForm.teamA} vs ${matchForm.teamB}: form, pressure, key players, and a cautious score prediction. Not betting advice.`,
        hashtags: '#Football #Prediction #MatchPreview #GameDay',
      },
    };
  }, [matchForm]);
  const modulePlan = useMemo(() => [
    'Own fixture and prediction schemas here, separate from cinematic scene prompts.',
    'Use low-animation data cards, comparison panels, and stat layouts.',
    'Keep predictions as entertainment and football discussion, not betting advice.',
    'Use manual-first data until approved providers are configured.',
    'Reuse shared metadata/export ideas only after manual review.',
  ], []);
  const predictionText = [
    predictionPackage.hook,
    predictionPackage.formSummary,
    predictionPackage.headToHead,
    `Key players: ${predictionPackage.keyPlayers.join(', ')}`,
    `Pressure: ${predictionPackage.pressureFactors.join(', ')}`,
    `Pick: ${predictionPackage.predictedScore} (${predictionPackage.confidence})`,
    predictionPackage.cta,
    predictionPackage.disclaimer,
  ].join('\n');
  const predictionCards = useMemo(() => [
    {
      label: 'Hook Card',
      title: predictionPackage.hook.toUpperCase(),
      body: `${matchForm.competition}${matchForm.matchDate ? ` · ${matchForm.matchDate}` : ''}`,
    },
    {
      label: 'Form Comparison',
      title: 'RECENT FORM',
      body: predictionPackage.formSummary,
    },
    {
      label: 'Head To Head',
      title: 'MATCHUP HISTORY',
      body: predictionPackage.headToHead,
    },
    {
      label: 'Key Players',
      title: 'WATCHLIST',
      body: predictionPackage.keyPlayers.join(' vs '),
    },
    {
      label: 'Pressure Factor',
      title: 'WHAT DECIDES IT?',
      body: predictionPackage.pressureFactors.join(' · '),
    },
    {
      label: 'Predicted Score',
      title: predictionPackage.predictedScore,
      body: `${predictionPackage.confidence} confidence · discussion pick only`,
    },
    {
      label: 'CTA Card',
      title: 'AGREE OR DISAGREE?',
      body: `${predictionPackage.cta} ${predictionPackage.disclaimer}`,
    },
  ], [matchForm, predictionPackage]);
  const cardsText = predictionCards.map((card, index) => `Card ${index + 1}: ${card.label}\n${card.title}\n${card.body}`).join('\n\n');

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

        <div className="mb-4 flex flex-wrap gap-2">
          {Object.values(MATCH_SCENARIOS).map((scenario) => (
            <button
              key={scenario.label}
              type="button"
              onClick={() => setMatchForm(scenario.data)}
              className="rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] hover:border-[#58A6FF] hover:text-white"
            >
              {scenario.label}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setWorkflow('Gameweek prediction batch')}
            className="rounded-lg border border-[#30363D] bg-[#161B22] px-3 py-2 text-xs font-semibold text-[#C9D1D9] hover:border-[#58A6FF] hover:text-white"
          >
            EPL Gameweek sample
          </button>
        </div>

        <section className="grid min-w-0 gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
            <label className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">Workflow</label>
            <select
              value={workflow}
              onChange={(event) => setWorkflow(event.target.value)}
              className="mt-2 w-full rounded-lg border border-[#30363D] bg-[#010409] px-3 py-2 text-sm text-white outline-none focus:border-[#58A6FF]"
            >
              {WORKFLOWS.map((item) => <option key={item}>{item}</option>)}
            </select>
            {workflow === 'Gameweek prediction batch' && (
              <div className="mt-3 rounded-lg border border-[#30363D] bg-[#010409] p-3 text-xs leading-5 text-[#C9D1D9]">
                <p className="font-semibold text-white">Sample matches</p>
                {GAMEWEEK_SAMPLE.map((item) => <p key={item}>{item}</p>)}
              </div>
            )}
            <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs leading-5 text-amber-200">
              No betting advice, no guaranteed outcomes, no paid data APIs, and no auto-posting.
            </div>
          </aside>

          <main className="min-w-0 space-y-4">
            <section className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
              <div className="mb-3">
                <h2 className="text-lg font-bold text-white">Single Match Prediction</h2>
                <p className="text-xs text-[#8B949E]">Manual-first football analysis. No betting advice, no live paid data API, no guarantees.</p>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {[
                  ['teamA', 'Team A'],
                  ['teamB', 'Team B'],
                  ['competition', 'Competition'],
                  ['matchDate', 'Match date'],
                  ['recentFormA', 'Team A form'],
                  ['recentFormB', 'Team B form'],
                  ['keyPlayers', 'Key players'],
                  ['context', 'Pressure/context'],
                ].map(([key, label]) => (
                  <label key={key} className="text-xs font-bold uppercase tracking-wide text-[#8B949E]">
                    {label}
                    <input
                      value={matchForm[key]}
                      onChange={(event) => updateMatch(key, event.target.value)}
                      className="mt-1 w-full rounded-lg border border-[#30363D] bg-[#010409] px-3 py-2 text-sm normal-case tracking-normal text-white outline-none focus:border-[#58A6FF]"
                    />
                  </label>
                ))}
                <label className="text-xs font-bold uppercase tracking-wide text-[#8B949E] md:col-span-2">
                  Head-to-head notes
                  <textarea
                    value={matchForm.headToHead}
                    onChange={(event) => updateMatch('headToHead', event.target.value)}
                    rows={3}
                    className="mt-1 w-full rounded-lg border border-[#30363D] bg-[#010409] px-3 py-2 text-sm normal-case tracking-normal text-white outline-none focus:border-[#58A6FF]"
                  />
                </label>
              </div>
            </section>

            <section className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
              <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">Prediction Data Cards</h2>
                  <p className="text-xs text-[#8B949E]">Low-animation 9:16 card sequence for clear comparison, stats, pick, and debate CTA.</p>
                </div>
                <CopyButton text={cardsText}>Copy Cards</CopyButton>
              </div>
              <div className="grid min-w-0 gap-3 md:grid-cols-2 xl:grid-cols-3">
                {predictionCards.map((card, index) => (
                  <article key={card.label} className="flex min-h-[360px] rounded-lg border border-[#30363D] bg-[#010409] p-4 text-white md:aspect-[9/16]">
                    <div className="flex h-full flex-col justify-between">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-wide text-[#58A6FF]">Card {index + 1} · {card.label}</p>
                        <h3 className="mt-4 break-words text-xl font-black leading-tight sm:text-2xl">{card.title}</h3>
                      </div>
                      <p className="my-4 overflow-hidden break-words rounded-lg border border-[#21262D] bg-[#0D1117] p-3 text-sm leading-6 text-[#C9D1D9]">{card.body}</p>
                      <p className="text-[10px] uppercase tracking-wide text-[#8B949E]">Generic team-color bars only · no official logos</p>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
              <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white">Prediction Package</h2>
                  <p className="text-xs text-[#8B949E]">Cautious analysis framing for debate and comments.</p>
                </div>
                <CopyButton text={predictionText}>Copy Package</CopyButton>
              </div>
              <div className="space-y-2 text-sm leading-6">
                <p className="text-white font-semibold">{predictionPackage.hook}</p>
                <p>{predictionPackage.formSummary}</p>
                <p>{predictionPackage.headToHead}</p>
                <p>Key players: {predictionPackage.keyPlayers.join(', ')}</p>
                <p>Prediction framing: {predictionPackage.predictedScore} · {predictionPackage.confidence} confidence</p>
                <p>{predictionPackage.cta}</p>
                <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">{predictionPackage.disclaimer}</p>
              </div>
            </section>

            <section className="rounded-lg border border-[#21262D] bg-[#0D1117] p-4">
              <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
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

        <div className="mt-4">
          <WorkflowQAPanel title="Prediction Studio Manual QA" items={PREDICTION_QA_ITEMS} />
        </div>
      </div>
    </div>
  );
}
