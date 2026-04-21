import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import ThreadangleLogo from './ThreadangleLogo';

const NICHES = [
  { emoji: '🎭', label: 'Entertainment' },
  { emoji: '😂', label: 'Comedy' },
  { emoji: '⚽', label: 'Sports' },
  { emoji: '💄', label: 'Beauty & Lifestyle' },
  { emoji: '💰', label: 'Finance & Investing' },
  { emoji: '🚀', label: 'Tech & AI' },
  { emoji: '💼', label: 'Business & Startups' },
  { emoji: '🏋️', label: 'Health & Fitness' },
  { emoji: '🎮', label: 'Gaming' },
  { emoji: '🌍', label: 'Travel' },
  { emoji: '🍳', label: 'Food & Cooking' },
  { emoji: '📚', label: 'Education' },
  { emoji: '🎵', label: 'Music' },
  { emoji: '🛍️', label: 'E-commerce' },
  { emoji: '🧠', label: 'Self-Improvement' },
  { emoji: '✏️', label: 'Other' },
];

function StepDots({ total, current }) {
  return (
    <div className="flex justify-center gap-2 mb-8">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`h-1.5 rounded-full transition-all duration-300 ${
            i === current ? 'w-8 bg-[#3B82F6]' : i < current ? 'w-4 bg-[#3B82F6]/40' : 'w-4 bg-[#27272A]'
          }`}
        />
      ))}
    </div>
  );
}

export default function Onboarding({ onComplete }) {
  // Steps: 0=Welcome, 1=Niche, 2=VoiceSetup, 3=Processing, 4=AllSet
  const [step, setStep] = useState(0);
  const [completing, setCompleting] = useState(false);

  // Niche step state
  const [selectedNiches, setSelectedNiches] = useState([]);

  // Voice step state
  const [voiceTab, setVoiceTab] = useState('urls');
  const [voiceUrls, setVoiceUrls] = useState('');
  const [voiceSample, setVoiceSample] = useState('');
  const [hasVoiceData, setHasVoiceData] = useState(false);

  // Processing step state
  const [processingStep, setProcessingStep] = useState(0);
  const processingItems = [
    'Extracting your vocabulary patterns',
    'Mapping your sentence rhythm',
    'Building your voice profile',
  ];

  useEffect(() => {
    if (step !== 3) return;
    const timers = [
      setTimeout(() => setProcessingStep(1), 800),
      setTimeout(() => setProcessingStep(2), 1600),
      setTimeout(() => setProcessingStep(3), 2400),
      setTimeout(() => setStep(4), 2700),
    ];
    return () => timers.forEach(clearTimeout);
  }, [step]);

  const skipAll = async () => {
    setCompleting(true);
    try { await api.completeOnboarding(); } catch {}
    onComplete();
  };

  const handleNicheContinue = async () => {
    if (selectedNiches.length > 0) {
      try { await api.saveNiche(selectedNiches); } catch {}
    }
    setStep(2);
  };

  const handleVoiceContinue = async () => {
    const urls = voiceUrls.split('\n').map(u => u.trim()).filter(u => u.startsWith('http'));
    const sample = voiceSample.trim();
    const hasContent = urls.length > 0 || sample.length >= 50;

    if (hasContent) {
      setHasVoiceData(true);
      try { await api.saveVoiceSamples({ urls, sample_text: sample }); } catch {}
      setStep(3);
    } else {
      setStep(4);
    }
  };

  const handleFinish = async () => {
    setCompleting(true);
    try { await api.completeOnboarding(); } catch {}
    onComplete();
  };

  const TOTAL_STEPS = 5;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#18181B] border border-[#27272A] rounded-2xl shadow-2xl w-full max-w-lg max-h-[92vh] overflow-y-auto">
        <div className="flex justify-center pt-8 pb-2">
          <ThreadangleLogo size={28} showText={false} />
        </div>

        <div className="p-6 pt-4">
          <StepDots total={TOTAL_STEPS} current={step} />

          {/* STEP 0: Welcome */}
          {step === 0 && (
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-[#3B82F6]/10 flex items-center justify-center mx-auto mb-6">
                <svg className="w-8 h-8 text-[#3B82F6]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h2 className="text-white text-2xl font-bold mb-3">Welcome to Threadangle</h2>
              <p className="text-[#A1A1AA] text-sm leading-relaxed mb-8">
                Turn any article, blog post, YouTube video, or idea into high-performing social content across every platform — in under 20 seconds. Set up your profile so the AI writes <em className="text-white not-italic font-semibold">exactly like you</em>.
              </p>
              <button
                onClick={() => setStep(1)}
                className="w-full py-4 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold rounded-xl transition-all shadow-lg shadow-[#3B82F6]/20"
              >
                Set Up My Profile →
              </button>
              <button onClick={skipAll} className="mt-4 text-[#71717A] text-xs hover:text-[#A1A1AA] transition-colors">
                Skip setup — I'll do this later
              </button>
            </div>
          )}

          {/* STEP 1: Niche Selection */}
          {step === 1 && (
            <div>
              <div className="text-center mb-5">
                <h2 className="text-white text-xl font-bold mb-2">Who is your content for?</h2>
                <p className="text-[#A1A1AA] text-sm">Pick all that apply. We'll tailor every generation for your audience.</p>
              </div>
              <div className="grid grid-cols-2 gap-2 mb-5">
                {NICHES.map(({ emoji, label }) => {
                  const selected = selectedNiches.includes(label);
                  return (
                    <button
                      key={label}
                      onClick={() => setSelectedNiches(prev =>
                        prev.includes(label) ? prev.filter(n => n !== label) : [...prev, label]
                      )}
                      className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl border-2 text-left transition-all text-sm font-medium ${
                        selected
                          ? 'border-[#3B82F6] bg-[#3B82F6]/10 text-white'
                          : 'border-[#27272A] text-[#A1A1AA] hover:border-[#3F3F46] hover:text-white bg-[#09090B]'
                      }`}
                    >
                      <span className="text-base flex-shrink-0">{emoji}</span>
                      <span className="truncate">{label}</span>
                      {selected && (
                        <svg className="w-3.5 h-3.5 text-[#3B82F6] flex-shrink-0 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  );
                })}
              </div>
              {selectedNiches.length > 0 && (
                <p className="text-center text-xs text-[#3B82F6] mb-4 font-medium">
                  {selectedNiches.length} selected · {selectedNiches.slice(0, 2).join(', ')}{selectedNiches.length > 2 ? ` +${selectedNiches.length - 2} more` : ''}
                </p>
              )}
              <button
                onClick={handleNicheContinue}
                className="w-full py-3.5 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold rounded-xl transition-all"
              >
                {selectedNiches.length > 0 ? 'Save & Continue →' : 'Continue →'}
              </button>
              <button onClick={skipAll} className="mt-3 w-full text-[#71717A] text-xs hover:text-[#A1A1AA] transition-colors">
                Skip for now — set this later in Settings
              </button>
            </div>
          )}

          {/* STEP 2: Voice Setup */}
          {step === 2 && (
            <div>
              <div className="text-center mb-5">
                <div className="text-3xl mb-2">🎤</div>
                <h2 className="text-white text-xl font-bold mb-2">Teach the AI to write like YOU</h2>
                <p className="text-[#A1A1AA] text-sm leading-relaxed">
                  Add links to your past posts or paste a writing sample. The AI will match your exact tone, style, and vocabulary — making content that sounds human, not robotic.
                </p>
              </div>

              <div className="flex gap-1 p-1 bg-[#09090B] rounded-xl mb-4">
                {[
                  { key: 'urls', label: '🔗 Paste URLs' },
                  { key: 'sample', label: '✍️ Write a Sample' },
                ].map(tab => (
                  <button
                    key={tab.key}
                    onClick={() => setVoiceTab(tab.key)}
                    className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${
                      voiceTab === tab.key ? 'bg-[#27272A] text-white' : 'text-[#71717A] hover:text-[#A1A1AA]'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {voiceTab === 'urls' ? (
                <div>
                  <textarea
                    value={voiceUrls}
                    onChange={e => setVoiceUrls(e.target.value)}
                    placeholder={"Paste links to your past posts, one per line:\nhttps://twitter.com/you/status/...\nhttps://linkedin.com/posts/you-...\nhttps://yourblog.com/article-title"}
                    rows={5}
                    className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-4 py-3 text-white text-sm placeholder:text-[#52525B] focus:border-[#3B82F6] outline-none resize-none"
                  />
                  <p className="text-[11px] text-[#71717A] mt-1.5">Supports Twitter, LinkedIn, blog posts, YouTube — up to 5 URLs</p>
                </div>
              ) : (
                <div>
                  <textarea
                    value={voiceSample}
                    onChange={e => setVoiceSample(e.target.value)}
                    placeholder="Write 2–3 paragraphs in your natural voice. Don't overthink it — just write how you'd explain your topic to a friend..."
                    rows={6}
                    className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-4 py-3 text-white text-sm placeholder:text-[#52525B] focus:border-[#3B82F6] outline-none resize-none"
                  />
                  <p className={`text-[11px] mt-1.5 text-right ${voiceSample.length >= 100 ? 'text-green-400' : 'text-[#71717A]'}`}>
                    {voiceSample.length} chars {voiceSample.length < 100 ? `(${100 - voiceSample.length} more recommended)` : '✓ enough to analyze'}
                  </p>
                </div>
              )}

              <div className="mt-4 p-3 bg-green-500/5 border border-green-500/20 rounded-xl">
                <p className="text-xs text-green-300 leading-relaxed">
                  ✅ Once analyzed, your AI content will sound nothing like generic ChatGPT output. It will match your rhythm, word choice, and personality.
                </p>
              </div>

              <button
                onClick={handleVoiceContinue}
                className="mt-4 w-full py-3.5 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold rounded-xl transition-all"
              >
                Analyze My Voice →
              </button>
              <button
                onClick={() => setStep(4)}
                className="mt-3 w-full text-[#71717A] text-xs hover:text-[#A1A1AA] transition-colors"
              >
                Skip — voice learning activates automatically after 3 generations
              </button>
            </div>
          )}

          {/* STEP 3: Processing */}
          {step === 3 && (
            <div className="text-center py-4">
              <div className="w-14 h-14 rounded-2xl bg-purple-500/10 flex items-center justify-center mx-auto mb-6">
                <div className="w-8 h-8 border-purple-400 rounded-full animate-spin" style={{ border: '3px solid #8B5CF6', borderTopColor: 'transparent' }} />
              </div>
              <h2 className="text-white text-xl font-bold mb-2">Analyzing your writing style...</h2>
              <p className="text-[#71717A] text-sm mb-8">This takes just a moment</p>
              <div className="space-y-3 text-left max-w-xs mx-auto">
                {processingItems.map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    {processingStep > i ? (
                      <div className="w-5 h-5 rounded-full bg-green-500/20 border border-green-500/40 flex items-center justify-center flex-shrink-0">
                        <svg className="w-3 h-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    ) : (
                      <div className={`w-5 h-5 rounded-full border flex-shrink-0 ${processingStep === i ? 'border-purple-400 bg-purple-500/10 animate-pulse' : 'border-[#27272A]'}`} />
                    )}
                    <span className={`text-sm ${processingStep > i ? 'text-green-300' : processingStep === i ? 'text-white' : 'text-[#52525B]'}`}>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 4: All Set */}
          {step === 4 && (
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center mx-auto mb-5">
                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-white text-2xl font-bold mb-3">
                {hasVoiceData || selectedNiches.length > 0 ? 'Your Profile is Complete!' : "You're All Set!"}
              </h2>

              {(hasVoiceData || selectedNiches.length > 0) ? (
                <div className="bg-[#09090B] border border-[#27272A] rounded-xl p-4 mb-5 text-left space-y-3">
                  {selectedNiches.length > 0 && (
                    <div>
                      <p className="text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Target Niches</p>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedNiches.map(n => (
                          <span key={n} className="text-xs px-2 py-1 bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20 rounded-lg">{n}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {hasVoiceData && (
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                      <span className="text-sm text-green-300 font-medium">Voice Profile: Analyzing in background...</span>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-[#A1A1AA] text-sm leading-relaxed mb-5">
                  Set up your niche and voice profile anytime in Settings. Your first 3 generations are free — start creating now!
                </p>
              )}

              <div className="p-3 bg-[#09090B] border border-[#27272A] rounded-xl mb-5 flex items-center gap-3">
                <span className="text-lg flex-shrink-0">🔒</span>
                <p className="text-xs text-[#71717A] leading-relaxed text-left">Your voice profile is private and only used to personalize your content. We never share it.</p>
              </div>

              <button
                onClick={handleFinish}
                disabled={completing}
                className="w-full py-4 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold rounded-xl transition-all shadow-lg shadow-[#3B82F6]/20 disabled:opacity-50"
              >
                {completing ? 'Setting up...' : 'Start Creating Content →'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
