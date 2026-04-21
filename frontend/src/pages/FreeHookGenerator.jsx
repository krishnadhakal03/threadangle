import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function FreeHookGenerator() {
  const [topic, setTopic] = useState('');
  const [category, setCategory] = useState('Marketing');
  const [hooks, setHooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copiedIndex, setCopiedIndex] = useState(null);

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleGenerate();
    }
  };

  const MAX_TOPIC = 500;

  const handleGenerate = async () => {
    if (!topic.trim()) return setError('Please enter a topic');
    if (topic.length > MAX_TOPIC) return setError(`Topic must be ${MAX_TOPIC} characters or less.`);
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_BASE}/api/free/generate-hooks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, category }),
      });
      
      if (response.status === 429) {
        throw new Error('You\'ve used your 5 free generations for today. Come back tomorrow, or sign up for a free Threadangle account.');
      }
      
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || data?.message || 'Failed to generate hooks. Please try again.');
      }

      const safeHooks = Array.isArray(data?.hooks) ? data.hooks : [];
      if (safeHooks.length === 0) {
        throw new Error('No hooks were returned. Please try a different topic.');
      }

      setHooks(safeHooks);
    } catch (err) {
      setHooks([]);
      setError(err.message || 'Something went wrong while generating hooks.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getTypeColor = (type) => {
    const types = {
      'Curiosity Gap': '#3B82F6',
      'Bold Claim': '#8B5CF6',
      'Personal Story': '#10B981',
      'Number/Stat': '#F59E0B',
      'Pain Point': '#EF4444'
    };
    return types[type] || '#3B82F6';
  };

  return (
    <div className="min-h-screen bg-[#09090B] text-white font-sans selection:bg-accent/30 block">
      <Navbar />

      <main className="max-w-4xl mx-auto px-6 py-12 space-y-12">
        <header className="text-center space-y-4">
          <div className="inline-block bg-accent/10 text-accent text-[10px] font-black uppercase px-4 py-1.5 rounded-full tracking-widest mb-2">
            Free Viral Tool
          </div>
          <h1 className="text-5xl md:text-6xl font-black italic uppercase tracking-tighter leading-none">
            Free Viral <span className="text-accent">Hook</span> Generator
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto font-medium">
            Generate 5 high-converting hook variations in seconds, then turn your best hook into full multi-platform content inside Threadangle.
          </p>
        </header>

        <section className="bg-card border border-border rounded-3xl p-8 glassmorphism shadow-2xl space-y-6">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-gray-500 uppercase tracking-widest pl-1">What is your post about?</label>
              <textarea 
                placeholder="e.g. How I grew my newsletter from 0 to 5,000 subscribers in 90 days without ads..."
                className={`w-full bg-dark/50 border rounded-xl p-4 text-white focus:border-accent outline-none transition-all h-32 resize-none placeholder:text-gray-700 font-medium mt-2 ${
                  topic.length > MAX_TOPIC ? 'border-red-500' : 'border-border'
                }`}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <div className="flex justify-between items-center pl-1 mt-1">
                <p className="text-[11px] text-[#3F3F46]">Press <kbd className="bg-[#27272A] text-[#71717A] px-1.5 py-0.5 rounded text-[10px] font-mono">Ctrl+Enter</kbd> to generate</p>
                <span className={`text-[11px] font-mono ${topic.length > MAX_TOPIC ? 'text-red-400' : topic.length > MAX_TOPIC * 0.8 ? 'text-yellow-400' : 'text-[#3F3F46]'}`}>
                  {topic.length}/{MAX_TOPIC}
                </span>
              </div>
            </div>
            
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-1 space-y-2">
                 <label className="text-xs font-bold text-gray-500 uppercase tracking-widest pl-1">Niche Category</label>
                 <div className="relative">
                   <select 
                      className="w-full bg-dark/50 border border-border rounded-xl p-4 pr-10 text-white focus:border-accent outline-none appearance-none font-medium cursor-pointer"
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                   >
                      {['Marketing', 'Business', 'Personal Development', 'Tech', 'Finance', 'Health', 'Fitness & Wellness', 'Food & Recipes', 'Other'].map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                   </select>
                   <svg className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                   </svg>
                 </div>
                 <p className="text-[12px] text-[#71717A] pl-1 font-medium mt-1">
                   Choose your niche for more targeted, relevant hooks
                 </p>
              </div>
              <div className="flex-1 flex items-end">
                <button 
                  disabled={loading}
                  onClick={handleGenerate}
                  className="w-full bg-accent hover:bg-accent/90 text-white font-bold py-4 rounded-xl shadow-xl shadow-accent/20 transition-all active:scale-95 text-[16px]"
                >
                  {loading ? 'Crafting Hooks...' : 'Generate 5 Free Hooks ⚡'}
                </button>
              </div>
            </div>
          </div>

          {error && <p className="text-error text-center font-bold animate-bounce">{error}</p>}
        </section>

        {/* TRUST SIGNALS - HORIZONTAL CARDS */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#111113] border border-[#27272A] rounded-[8px] p-6 text-center flex flex-col items-center gap-2">
                <div className="text-[28px]">⚡</div>
                <h4 className="text-[14px] text-white font-semibold">Powered by Claude AI</h4>
                <p className="text-[12px] text-[#71717A]">Same AI used by Fortune 500 companies</p>
            </div>
            <div className="bg-[#111113] border border-[#27272A] rounded-[8px] p-6 text-center flex flex-col items-center gap-2">
                <div className="text-[28px]">🔒</div>
                <h4 className="text-[14px] text-white font-semibold">No Login Required</h4>
                <p className="text-[12px] text-[#71717A]">Test the quality instantly before creating your account</p>
            </div>
            <div className="bg-[#111113] border border-[#27272A] rounded-[8px] p-6 text-center flex flex-col items-center gap-2">
                <div className="text-[28px]">🎯</div>
                <h4 className="text-[14px] text-white font-semibold">5 Hook Variations</h4>
                <p className="text-[12px] text-[#71717A]">Each uses a different psychological trigger</p>
            </div>
        </section>

        <section className="bg-[#111113] border border-[#27272A] rounded-[8px] p-8 space-y-4">
          <h3 className="text-lg font-bold text-white text-center">What You Unlock in Threadangle</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-4">
              <p className="font-semibold text-white mb-1">One input → 5 outputs</p>
              <p className="text-[#A1A1AA]">Twitter/X, LinkedIn, TikTok, Instagram Reels, and YouTube Shorts from one source.</p>
            </div>
            <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-4">
              <p className="font-semibold text-white mb-1">Edit + save + schedule</p>
              <p className="text-[#A1A1AA]">Refine each output, keep history, and schedule your publishing workflow.</p>
            </div>
          </div>
        </section>

        {hooks.length === 0 && !loading && !error && (
          <section className="space-y-4 pt-4 animate-in fade-in duration-700">
            <div className="text-center mb-6">
                <span className="text-[11px] font-bold text-gray-500 uppercase tracking-[2px]">Here is what you will get</span>
            </div>
            <div className="grid grid-cols-1 gap-4">
                {/* Example 1 */}
                <div className="bg-[#111113] border border-[#27272A] rounded-[8px] p-[20px] flex flex-col relative group">
                    <div className="flex justify-between items-start mb-3">
                        <span className="inline-block text-[9px] font-black uppercase px-3 py-1 rounded-full tracking-widest text-white shadow-sm" style={{ backgroundColor: '#3B82F6' }}>
                            Curiosity Gap
                        </span>
                    </div>
                    <p className="text-[16px] text-white font-medium mb-4 leading-[1.6]">"Nobody tells you this about growing on Twitter — but I learned it the hard way after 2 years of zero growth."</p>
                    <div className="pt-3 border-t border-[#27272A]">
                        <span className="text-[12px] text-[#71717A] italic mr-1">Why it works:</span>
                        <span className="text-[13px] text-[#71717A] italic">Opens a knowledge gap the reader needs to close. Forces them to keep reading.</span>
                    </div>
                </div>

                {/* Example 2 */}
                <div className="bg-[#111113] border border-[#27272A] rounded-[8px] p-[20px] flex flex-col relative group">
                    <div className="flex justify-between items-start mb-3">
                        <span className="inline-block text-[9px] font-black uppercase px-3 py-1 rounded-full tracking-widest text-white shadow-sm" style={{ backgroundColor: '#10B981' }}>
                            Number/Stat
                        </span>
                    </div>
                    <p className="text-[16px] text-white font-medium mb-4 leading-[1.6]">"I gained 4,200 Twitter followers in 90 days using one simple content system. Here is exactly what I did."</p>
                    <div className="pt-3 border-t border-[#27272A]">
                        <span className="text-[12px] text-[#71717A] italic mr-1">Why it works:</span>
                        <span className="text-[13px] text-[#71717A] italic">Specific numbers create instant credibility and set a concrete expectation.</span>
                    </div>
                </div>
            </div>
            <p className="text-center text-[12px] text-[#71717A] mt-6">+ 3 more hooks generated for your specific topic</p>
          </section>
        )}

        {hooks.length > 0 && (
          <section className="space-y-6 pt-4 animate-in fade-in slide-in-from-bottom-8 duration-700">
            <h3 className="text-xl font-black text-white uppercase italic text-center mb-6">Your Viral Hooks</h3>
            <div className="grid grid-cols-1 gap-4">
              {hooks.map((hook, i) => (
                <div key={i} className="bg-[#111113] border border-[#27272A] hover:border-[#3F3F46] rounded-[8px] p-[24px] flex flex-col relative transition-all group">
                  <div className="flex justify-between items-start mb-3">
                    <span 
                        className="inline-block text-[10px] font-black uppercase px-3 py-1 rounded-full tracking-widest text-white shadow-sm"
                        style={{ backgroundColor: getTypeColor(hook.type) }}
                    >
                      {hook.type}
                    </span>
                    <button 
                        onClick={() => copyToClipboard(hook.text, i)}
                        className="text-[11px] font-bold text-gray-400 hover:text-white uppercase tracking-widest bg-dark/50 border border-border px-3 py-1 rounded-md transition-colors"
                    >
                        {copiedIndex === i ? 'Copied ✓' : 'Copy'}
                    </button>
                  </div>
                  <p className="text-[16px] text-[#FAFAFA] font-medium mb-4 leading-[1.6]">{hook.text}</p>
                <div className="pt-4 border-t border-[#27272A] flex items-center justify-between gap-4">
                    <div>
                      <span className="text-[12px] text-[#71717A] font-medium mr-2">Why it works:</span>
                      <span className="text-[13px] text-[#71717A] italic">{hook.why_it_works}</span>
                    </div>
                    <button
                      onClick={() => {
                        const params = new URLSearchParams();
                        params.set('hook', hook.text);
                        if (topic.trim()) params.set('topic', topic.trim());
                        if (category) params.set('niche', category);
                        window.location.href = `/signup?${params.toString()}`;
                      }}
                      className="flex-shrink-0 text-[12px] font-bold text-[#3B82F6] hover:text-white bg-[#3B82F6]/10 hover:bg-[#3B82F6] border border-[#3B82F6]/30 hover:border-[#3B82F6] px-3 py-1.5 rounded-lg transition-all whitespace-nowrap"
                    >
                      Use in Threadangle →
                    </button>
                  </div>
                </div>
              ))}
            </div>
            
            <p className="text-center text-[13px] text-[#71717A] italic mt-8 font-medium">
                Got a great hook? Share it on Twitter and tag @threadangle
            </p>
          </section>
        )}

        {/* UPGRADE CALLOUT SECTION */}
        <section className="mt-16 w-full rounded-[12px] border border-[#2563EB] p-10 flex flex-col items-center text-center shadow-2xl relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #1a1a2e 100%)' }}>
            <span className="text-[10px] font-bold text-blue-300 uppercase tracking-[2px] mb-4">WANT THE FULL THREAD?</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
              Turn This Hook Into a Full Multi-Platform Content Pack
            </h2>
            <p className="text-blue-100/80 text-lg max-w-2xl font-medium mb-10 leading-relaxed">
              Threadangle turns your best hook into platform-specific content with editing, history, and scheduling. Start free and see your full workflow in one dashboard.
            </p>
            
            <div className="flex flex-col md:flex-row gap-8 mb-10 text-left w-full max-w-lg justify-center">
                <div className="flex flex-col items-center md:items-start">
                    <span className="text-3xl font-black text-white">20 <span className="text-xl">seconds</span></span>
                    <p className="text-blue-200 text-sm font-medium">to generate a complete thread</p>
                </div>
                <div className="hidden md:block w-px bg-blue-500/30"></div>
                <div className="flex flex-col items-center md:items-start">
                  <span className="text-3xl font-black text-white">5 <span className="text-xl">platforms</span></span>
                  <p className="text-blue-200 text-sm font-medium">X, LinkedIn, TikTok, Reels, Shorts</p>
                </div>
            </div>

            <button 
                onClick={() => {
                  const params = new URLSearchParams();
                  if (topic.trim()) params.set('topic', topic.trim());
                  if (category) params.set('niche', category);
                  window.location.href = `/signup?${params.toString()}`;
                }}
                className="w-full md:w-auto bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold py-[16px] px-[40px] rounded-[10px] transition-all shadow-xl shadow-blue-500/20 text-[16px]"
            >
                Try Threadangle Free →
            </button>
            <p className="text-[12px] text-blue-200 mt-4 opacity-70">
              5 free generations · No credit card · Cancel anytime
            </p>
        </section>

      </main>

      <Footer />
    </div>
  );
}
