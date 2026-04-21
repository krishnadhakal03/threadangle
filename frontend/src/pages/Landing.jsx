import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useCMS } from '../hooks/useCMS';
import { useSEO } from '../hooks/useSEO';
import { api } from '../utils/api';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SocialPlatformIcon from '../components/SocialPlatformIcon';

const FAQItem = ({ question, answer, isOpen, onClick }) => (
  <div className="border-b border-border/50 overflow-hidden">
    <button
      className="w-full py-5 px-4 text-left flex justify-between items-center bg-card/30 hover:bg-card/50 transition-all font-medium"
      onClick={onClick}
    >
      <span>{question}</span>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-accent flex-shrink-0"
        style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }}>
        <polyline points="6 9 12 15 18 9"></polyline>
      </svg>
    </button>
    <div className={`bg-dark/40 px-4 transition-all duration-300 ease-in-out ${isOpen ? 'max-h-96 py-4' : 'max-h-0 py-0'}`}>
      <p className="text-gray-400 text-sm leading-relaxed">{answer}</p>
    </div>
  </div>
);

const Landing = () => {
  const [openFAQ, setOpenFAQ] = useState(null);
  const [latestPosts, setLatestPosts] = useState([]);
  const { content: seo } = useCMS('seo', {
    home_meta_title: 'Threadangle — Turn Any Content Into Viral Social Posts In Seconds',
    home_meta_description: 'Paste a blog post, YouTube link, or idea. Get Twitter threads, LinkedIn posts, TikTok scripts, Reels, and Shorts in ~20 seconds.'
  });

  const { content } = useCMS('home', {
    hero_badge: 'Works for any creator — not just marketers',
    hero_headline: 'One Input. Five Platform-Ready Posts. In ~20 Seconds.',
    hero_subheadline: 'Paste a blog post, YouTube video, or raw idea. Get Twitter threads, LinkedIn posts, TikTok scripts, Reels & Shorts — plus full AI video generation powered by RunwayML Gen 4.5. One platform for everything you publish.',
    hero_primary_cta: 'Start Free — 5 Generations',
    hero_secondary_cta: 'See Interactive Demo',
    hero_social_proof: 'Free plan includes 5 generations • No credit card required',
    how_title: 'How Threadangle Works',
    step1_title: 'Input',
    step1_description: 'Paste a URL, YouTube link, or raw text.',
    step2_title: 'Select Outputs',
    step2_description: 'Choose Twitter, LinkedIn, TikTok, Reels, and Shorts.',
    step3_title: 'Generate + Refine',
    step3_description: 'Edit instantly, save history, and schedule posts.',
    features_title: 'Built for Real Publishing Workflows',
    workflow_step1_title: 'Voice Learning',
    workflow_step1_description: 'Learns your writing style over time so generated content sounds exactly like you.',
    workflow_step2_title: 'Generate in 20s',
    workflow_step2_description: 'One click generates 5 platform-ready posts from any URL, video, or idea.',
    workflow_step3_title: 'Edit & A/B Hooks',
    workflow_step3_description: 'Refine content and generate hook variations to find what resonates.',
    workflow_step4_title: 'Schedule & Publish',
    workflow_step4_description: 'Schedule to your calendar and auto-post to LinkedIn with one click.',
    feature1_title: "Twitter Threads",
    feature1_description: "10-tweet threads with viral hooks, numbered points, and strong CTAs",
    feature2_title: "LinkedIn Posts",
    feature2_description: "Professional 200-300 word posts that drive engagement and followers",
    feature3_title: "TikTok Scripts",
    feature3_description: "Full scene-by-scene video scripts with hooks, b-roll suggestions, and captions",
    feature4_title: "Multiple Tones",
    feature4_description: "Professional, casual, viral, or educational — you choose the angle",
    stats_users: "1,200+",
    stats_users_label: "Creators Using Threadangle",
    stats_generations: "50,000+",
    stats_generations_label: "Posts Generated",
    stats_time_saved: "5+ Hours",
    stats_time_saved_label: "Saved Per Week Per User",
    bottom_cta_headline: 'Launch Better Content Faster',
    bottom_cta_subtext: 'Stop rewriting the same idea for every platform. Generate once, publish everywhere with platform-specific output.',
    bottom_cta_button: 'Create Free Account',
    faq_title: 'Frequently Asked Questions',
    testimonials: [
      { name: 'Jamie L.', role: 'Fitness Coach · @jamielifts', initials: 'JL', text: "ok i didn't believe the hype but i pasted my workout blog post and got a full twitter thread + tiktok script in like 30 seconds. the tiktok sounded like me which was the surprising part", platform: 'TikTok' },
      { name: 'Marcus T.', role: 'B2B Marketing · @marcust_mktg', initials: 'MT', text: 'My LinkedIn engagement went up noticeably after I started using Threadangle. The hooks are sharper than what I write from scratch. Saves me about 2 hours every week.', platform: 'LinkedIn' },
      { name: 'Priya M.', role: 'Design Solopreneur · @priyamade', initials: 'PM', text: "I do not have time to rewrite my blog for Instagram, LinkedIn and TikTok. Now I don't have to. One paste and it's done. The voice actually sounds like mine.", platform: 'Twitter' }
    ],
    home_faqs: [
      { q: 'What counts as one generation?', a: 'One URL or text input equals one generation, regardless of how many platforms you select. Choosing Twitter, LinkedIn and TikTok together still uses only one generation.' },
      { q: 'Do I need a credit card for the free plan?', a: 'No. Sign up with just your email and password. No payment details required until you choose to upgrade.' },
      { q: 'What happens when I use all 5 free generations?', a: 'You will see an upgrade prompt. All your generated content remains in your history, and you can upgrade anytime to keep generating.' },
      { q: 'Can I cancel my subscription anytime?', a: 'Yes. Go to Settings and click Manage Subscription. You will be taken to the Stripe portal where you can cancel with one click. Your plan stays active until the end of the billing period.' },
      { q: 'What AI model powers Threadangle?', a: 'Threadangle uses Claude by Anthropic, one of the most capable AI models available. It is the same technology used by leading AI companies worldwide.' },
      { q: 'Can I schedule posts inside Threadangle?', a: 'Yes. You can schedule content from History and view your posting plan in Calendar. LinkedIn auto-posting is currently the active supported channel.' },
      { q: 'What kind of content works best?', a: 'Blog posts, articles, YouTube transcripts, newsletters, podcast notes, and raw drafts all work well. If it has substance, Threadangle can turn it into platform-ready content.' },
      { q: 'Is my content stored or shared?', a: 'Your generated content is stored privately in your account history. It is never shared with other users or used to train AI models.' },
      { q: 'Can Threadangle create actual videos, not just scripts?', a: 'Yes. AI Video Studio is a full video creation pipeline — Claude writes your script, a storyboard previewer lets you approve every scene, then RunwayML Gen 4.5 renders photorealistic short-form video clips. The final MP4 is ready to upload to TikTok, Instagram Reels, and YouTube Shorts, with auto-generated captions and SEO metadata included.' },
      { q: 'Do I need a camera or video editing skills for AI Video Studio?', a: 'No camera, no editing skills, no crew needed. AI Video Studio is designed for faceless video creation. You provide a topic or script; the AI handles character generation, scene rendering, text overlays, and captioning automatically.' }
    ]
  });

  const marketingCopy = content;

  useEffect(() => {
    api.getPosts(null, null, 3).then(setLatestPosts).catch(() => {});
  }, []);

  const testimonials = Array.isArray(marketingCopy.testimonials) ? marketingCopy.testimonials : [];
  const faqs = Array.isArray(marketingCopy.home_faqs) ? marketingCopy.home_faqs : [];

  useSEO({
    title: seo.home_meta_title,
    description: seo.home_meta_description,
  });

  return (
    <div className="min-h-screen bg-[#09090B] text-white font-sans selection:bg-accent/30 selection:text-white">
      <Navbar />

      {/* ── HERO ─────────────────────────────────────────────────── */}
      <div className="flex flex-col items-center justify-center pt-32 pb-20 px-4 min-h-[85vh]">
        <div className="text-center mb-10 animate-in fade-in slide-in-from-top-4 duration-1000">
          <div className="inline-flex items-center gap-2 bg-accent/10 border border-accent/20 px-3 py-1 rounded-full text-[10px] font-bold text-accent uppercase tracking-widest mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
            </span>
              {marketingCopy.hero_badge}
          </div>
          <h1 className="font-bold tracking-tight mb-8 bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-500 max-w-5xl mx-auto leading-tight italic" style={{ fontSize: 'clamp(32px, 8vw, 64px)' }}>
              {marketingCopy.hero_headline}
          </h1>
          <p className="text-gray-400 max-w-3xl mx-auto leading-relaxed" style={{ fontSize: 'clamp(14px, 4vw, 18px)' }}>
              {marketingCopy.hero_subheadline}
          </p>
        </div>

        <div className="flex flex-col items-center gap-4 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-200">
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <Link to="/signup" className="flex items-center justify-center bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold text-[16px] h-[52px] px-8 rounded-[10px] shadow-xl shadow-blue-500/20 transition-all hover:scale-105 active:scale-95">
              {marketingCopy.hero_primary_cta}
            </Link>
            <Link to="/demo" className="flex items-center justify-center bg-transparent border border-[#3B82F6]/40 hover:border-[#3B82F6] hover:bg-[#3B82F6]/10 text-[#93C5FD] font-bold text-[16px] h-[52px] px-8 rounded-[10px] transition-all hover:scale-105 active:scale-95">
              🎬 {marketingCopy.hero_secondary_cta}
            </Link>
          </div>
          <Link to="/login" className="text-gray-400 hover:text-white text-sm font-medium transition-colors">
            Already have an account? Sign In →
          </Link>
          <p className="text-center text-sm text-gray-500 mt-6 font-medium">
            {marketingCopy.hero_social_proof}
          </p>
        </div>
      </div>

      {/* ── PLATFORM BADGES ──────────────────────────────────────── */}
      <div className="border-y border-[#27272A] bg-[#111113] py-6 px-6">
        <div className="max-w-4xl mx-auto flex flex-wrap items-center justify-center gap-4 md:gap-8">
          <span className="text-[11px] font-bold text-[#52525B] uppercase tracking-widest">Works with</span>
          {[
            { label: 'Twitter / X', platform: 'twitter', color: '#FAFAFA' },
            { label: 'LinkedIn', platform: 'linkedin', color: '#0A66C2' },
            { label: 'TikTok', platform: 'tiktok', color: '#FF0050' },
            { label: 'Instagram Reels', platform: 'reels', color: '#E1306C' },
            { label: 'YouTube Shorts', platform: 'shorts', color: '#FF0000' },
          ].map(p => (
            <div key={p.label} className="flex items-center gap-2 bg-[#18181B] border border-[#27272A] rounded-full px-4 py-2">
              <span style={{ color: p.color }} className="font-bold text-sm"><SocialPlatformIcon platform={p.platform} className="w-4 h-4" /></span>
              <span className="text-[#A1A1AA] text-sm font-medium">{p.label}</span>
            </div>
          ))}
          <div className="flex items-center gap-2 bg-[#18181B] border border-purple-500/30 rounded-full px-4 py-2">
            <svg className="w-4 h-4 text-purple-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            <span className="text-[#A1A1AA] text-sm font-medium">AI Video Studio</span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">New</span>
          </div>
          <div className="flex items-center gap-2 bg-[#18181B] border border-[#27272A] rounded-full px-4 py-2">
            <span className="text-[#10B981] font-bold text-sm">⚡</span>
            <span className="text-[#A1A1AA] text-sm font-medium">Powered by Claude AI</span>
          </div>
        </div>
      </div>

      {/* ── FULL WORKFLOW (id="features") ───────────────────────── */}
      <section id="features" className="pt-20 pb-20 px-6 bg-[#09090B]">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <span className="text-[10px] font-bold text-[#3B82F6] uppercase tracking-[0.2em] mb-4 block">COMPLETE WORKFLOW</span>
            <h2 className="text-3xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
              How Threadangle Works
            </h2>
            <p className="text-[#71717A] mt-4 text-base max-w-xl mx-auto">From blank page to published — four steps that run in under two minutes.</p>
          </div>

          <div className="relative">
            {/* Connector line desktop */}
            <div className="hidden md:block absolute top-10 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-transparent via-[#3B82F6]/40 to-transparent" />

            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              {[
                {
                  icon: '🎤',
                  step: '1',
                  title: marketingCopy.workflow_step1_title,
                  desc: marketingCopy.workflow_step1_description,
                  stepColor: '#8B5CF6',
                  iconBg: 'bg-purple-500/10 border-purple-500/25',
                },
                {
                  icon: '⚡',
                  step: '2',
                  title: marketingCopy.workflow_step2_title,
                  desc: marketingCopy.workflow_step2_description,
                  stepColor: '#3B82F6',
                  iconBg: 'bg-blue-500/10 border-blue-500/25',
                },
                {
                  icon: '✏️',
                  step: '3',
                  title: marketingCopy.workflow_step3_title,
                  desc: marketingCopy.workflow_step3_description,
                  stepColor: '#10B981',
                  iconBg: 'bg-emerald-500/10 border-emerald-500/25',
                },
                {
                  icon: '📅',
                  step: '4',
                  title: marketingCopy.workflow_step4_title,
                  desc: marketingCopy.workflow_step4_description,
                  stepColor: '#F59E0B',
                  iconBg: 'bg-amber-500/10 border-amber-500/25',
                },
              ].map((item) => (
                <div key={item.step} className="flex flex-col items-center text-center">
                  <div className="relative mb-5">
                    <div className={`w-20 h-20 rounded-2xl border flex items-center justify-center text-3xl shadow-xl ${item.iconBg}`}>
                      {item.icon}
                    </div>
                    <span
                      className="absolute -top-2 -right-2 text-white text-[11px] font-black rounded-full w-6 h-6 flex items-center justify-center shadow-lg"
                      style={{ background: item.stepColor }}
                    >
                      {item.step}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white mb-2">{item.title}</h3>
                  <p className="text-[#71717A] text-sm leading-relaxed px-1">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Video Studio — 5th workflow step highlight */}
          <div className="mt-8 p-5 md:p-6 bg-gradient-to-r from-purple-500/8 via-[#0D1117] to-blue-500/8 border border-purple-500/25 rounded-2xl flex flex-col md:flex-row items-center gap-5 group hover:border-purple-500/40 transition-all">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30 flex items-center justify-center flex-shrink-0 shadow-lg shadow-purple-500/10">
              <svg className="w-7 h-7 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            </div>
            <div className="flex-1 text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-2 mb-1">
                <span className="text-[10px] font-bold text-purple-400 uppercase tracking-widest">Plus</span>
                <h3 className="text-white font-bold text-lg">AI Video Studio</h3>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">Production</span>
              </div>
              <p className="text-[#8B949E] text-sm">Script → storyboard approval → RunwayML Gen 4.5 cinematic render. Faceless short-form videos ready for TikTok, Reels &amp; Shorts — no camera needed.</p>
            </div>
            <a href="#video-studio" className="flex-shrink-0 px-5 py-2.5 bg-gradient-to-r from-purple-600/20 to-blue-600/20 border border-purple-500/30 rounded-xl text-purple-300 text-sm font-semibold hover:from-purple-600/30 hover:to-blue-600/30 transition-all whitespace-nowrap">
              See How →
            </a>
          </div>
        </div>
      </section>

      {/* ── FEATURES GRID ────────────────────────────────────────── */}
      <div className="pt-10 pb-20 px-6 bg-[#111113] border-y border-[#1C1C1F]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-[10px] font-bold text-[#52525B] uppercase tracking-[0.2em] mb-4 block">WHAT YOU GET</span>
            <h2 className="text-3xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
              {marketingCopy.features_title}
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                title: '5 Platform Outputs from One Input',
                desc: 'Generate Twitter/X threads, LinkedIn posts, TikTok scripts, Instagram Reels captions & hashtags, and YouTube Shorts titles & descriptions — all in one run.',
                platform: 'twitter',
                color: '#FAFAFA',
                bg: '#18181B'
              },
              {
                title: 'Built-In Editing + Hook Variations',
                desc: 'Get multiple hook options, edit inline, and save your best version without leaving the app.',
                platform: 'linkedin',
                color: '#0A66C2',
                bg: '#18181B'
              },
              {
                title: 'History + Calendar Scheduling',
                desc: 'Keep every generation organized and schedule publishing workflows from a single dashboard.',
                platform: 'tiktok',
                color: '#FF0050',
                bg: '#18181B'
              },
              {
                title: 'Voice Learning Personalization',
                desc: 'After initial successful generations, Threadangle adapts to your style so outputs sound more like you.',
                icon: '🎤',
                color: '#3B82F6',
                bg: '#18181B'
              },
            ].map((f, i) => (
              <div key={i} className="bg-[#18181B] border border-[#27272A] rounded-2xl p-8 flex gap-5 hover:border-[#3B82F6]/40 transition-all group">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold flex-shrink-0 bg-[#09090B] border border-[#27272A] group-hover:border-[#3B82F6]/40 transition-all" style={{ color: f.color }}>
                  {f.platform ? <SocialPlatformIcon platform={f.platform} className="w-6 h-6" /> : f.icon}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">{f.title}</h3>
                  <p className="text-[#71717A] text-sm leading-relaxed">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Video Studio — full-width feature card */}
          <div className="mt-6 bg-gradient-to-r from-[#0D1117] to-[#161B22] border border-purple-500/30 rounded-2xl p-8 flex flex-col md:flex-row gap-6 hover:border-purple-500/50 transition-all group">
            <div className="flex items-start gap-4 flex-1">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30 flex items-center justify-center flex-shrink-0 shadow-lg shadow-purple-500/10">
                <svg className="w-7 h-7 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <h3 className="text-lg font-bold text-white">AI Video Studio</h3>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">Production</span>
                </div>
                <p className="text-[#8B949E] text-sm leading-relaxed mb-4">Claude plans your script with retention hooks → storyboard previewer for scene-by-scene approval → RunwayML Gen 4.5 renders cinematic clips → export-ready MP4 with auto captions for TikTok, Reels &amp; Shorts.</p>
                <div className="flex flex-wrap gap-2">
                  {['RunwayML Gen 4.5', 'Claude Script Planner', 'Storyboard Previewer', 'Auto Captions', 'Batch Generation', 'SEO Optimizer'].map(f => (
                    <span key={f} className="text-[11px] px-2.5 py-1 bg-[#0D1117] border border-[#21262D] rounded-full text-[#8B949E]">{f}</span>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex flex-col justify-center items-center md:items-end gap-2 flex-shrink-0">
              <a href="#video-studio" className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold rounded-xl text-sm shadow-lg shadow-purple-500/20 transition-all hover:scale-105 whitespace-nowrap">
                See Full Demo →
              </a>
              <p className="text-[11px] text-[#484F58]">Included in Solo &amp; Founder plans</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── AI VIDEO STUDIO SHOWCASE (id="video-studio") ─────────── */}
      <div id="video-studio" className="py-20 px-6 bg-[#09090B]">
        <div className="max-w-6xl mx-auto">
          <div className="relative rounded-3xl overflow-hidden border border-purple-500/20">
            {/* Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-[#0D1117] via-[#161B22] to-[#0D1117]" />
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500/5 via-transparent to-blue-500/5" />
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-purple-500/50 to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />

            <div className="relative z-10 p-8 md:p-14">
              {/* Header */}
              <div className="text-center mb-12">
                <div className="inline-flex items-center gap-2 bg-purple-500/10 border border-purple-500/20 px-4 py-1.5 rounded-full mb-6">
                  <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                  <span className="text-purple-300 text-[11px] font-bold uppercase tracking-widest">AI Video Studio</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase">Production</span>
                </div>
                <h2 className="text-3xl md:text-5xl font-bold text-white mb-5 leading-tight">
                  Script to Cinematic Video.<br className="hidden md:block" />
                  <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-400"> No Camera. No Crew.</span>
                </h2>
                <p className="text-[#8B949E] text-lg max-w-2xl mx-auto leading-relaxed">
                  Claude plans your hook, body &amp; CTA with retention notes — storyboard previewer lets you approve every scene — then RunwayML Gen 4.5 renders it into a cinematic faceless video.
                </p>
              </div>

              {/* 3-step pipeline */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
                {[
                  {
                    icon: '🤖', step: '01', color: '#A78BFA', borderColor: 'border-purple-500/30', bg: 'bg-purple-500/5',
                    title: 'Claude Plans Your Script',
                    desc: 'AI writes your hook, body & CTA with retention notes and platform SEO metadata for Shorts, Reels & TikTok. Edit or regenerate any section.',
                  },
                  {
                    icon: '🎞️', step: '02', color: '#60A5FA', borderColor: 'border-blue-500/30', bg: 'bg-blue-500/5',
                    title: 'Approve Every Scene',
                    desc: 'Drag-and-drop storyboard previewer. Review, reorder, and edit each individual scene before committing a single credit to render.',
                  },
                  {
                    icon: '🎬', step: '03', color: '#34D399', borderColor: 'border-emerald-500/30', bg: 'bg-emerald-500/5',
                    title: 'RunwayML Gen 4.5 Renders',
                    desc: 'Photorealistic AI video with characters, text overlays, and auto-captioning — export-ready MP4 for TikTok, Reels & Shorts in minutes.',
                  },
                ].map((s) => (
                  <div key={s.step} className={`p-6 rounded-2xl ${s.bg} border ${s.borderColor}`}>
                    <div className="flex items-center gap-3 mb-4">
                      <span className="text-3xl">{s.icon}</span>
                      <span className="text-[11px] font-bold uppercase tracking-widest" style={{ color: s.color }}>{s.step}</span>
                    </div>
                    <h3 className="text-white font-bold text-base mb-2">{s.title}</h3>
                    <p className="text-[#8B949E] text-sm leading-relaxed">{s.desc}</p>
                  </div>
                ))}
              </div>

              {/* Features + checklist */}
              <div className="grid md:grid-cols-2 gap-10 mb-12">
                <div>
                  <p className="text-[10px] font-bold text-[#484F58] uppercase tracking-widest mb-4">Powered By</p>
                  <div className="flex flex-wrap gap-2">
                    {['🎬 RunwayML Gen 4.5', '🤖 Claude AI Planner', '🎭 Character System', '🎞️ Storyboard Previewer', '🔤 Auto Captions + SRT', '⚡ Batch Generation', '📊 SEO Optimizer', '📱 TikTok · Reels · Shorts'].map(f => (
                      <span key={f} className="text-xs px-3 py-1.5 bg-[#0D1117] border border-[#21262D] rounded-full text-[#8B949E]">{f}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-bold text-[#484F58] uppercase tracking-widest mb-4">Every Video Includes</p>
                  <div className="space-y-2.5">
                    {[
                      'Shot-by-shot storyboard you approve before render',
                      'AI character generation or upload your own photo',
                      'Auto SRT captions + synchronized text overlays',
                      'YouTube Shorts, Instagram Reels & TikTok MP4 export',
                      'Platform SEO metadata: titles, descriptions & tags',
                      'Batch queue — generate multiple videos at once',
                    ].map((item) => (
                      <div key={item} className="flex items-center gap-2.5">
                        <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                        <span className="text-sm text-[#C9D1D9]">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* CTA */}
              <div className="text-center">
                <Link
                  to="/signup"
                  className="inline-flex items-center justify-center gap-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold text-[16px] h-[54px] px-10 rounded-xl shadow-xl shadow-purple-500/25 transition-all hover:scale-105 active:scale-95"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                  Start Free — Try Video Studio
                </Link>
                <p className="text-[#484F58] text-xs mt-3">Included with Solo &amp; Founder plans · No credit card required for free tier · 5 free content generations on signup</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── VOICE / TRUST SECTION ────────────────────────────────── */}
      <div className="py-20 px-6 bg-[#09090B]">
        <div className="max-w-5xl mx-auto">
          <div className="bg-gradient-to-br from-[#18181B] to-[#111113] border border-[#27272A] rounded-3xl p-10 md:p-14 flex flex-col md:flex-row items-center gap-10">
            <div className="flex-1">
              <span className="text-[10px] font-bold text-[#3B82F6] uppercase tracking-[0.2em] mb-3 block">YOUR BIGGEST QUESTION, ANSWERED</span>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-5 leading-tight">
                Will it sound like me — or like a robot?
              </h2>
              <p className="text-[#71717A] leading-relaxed mb-6">
                Fair question. The short answer: it starts good and gets better the more you use it.
              </p>
              <ul className="space-y-4">
                {[
                  { icon: '🎤', text: 'On first use, you choose your tone (casual, professional, viral) and the AI adapts the voice to your platform.' },
                  { icon: '📝', text: 'Paste a few writing samples during onboarding and Threadangle learns your sentence patterns, word choices, and style.' },
                  { icon: '✏️', text: 'Every output is fully editable inline — you stay in control of every word before it goes live.' },
                  { icon: '🔄', text: 'The more you use it, the better it matches your voice. Early adopters say it feels like a writing partner within a week.' },
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="text-xl mt-0.5 flex-shrink-0">{item.icon}</span>
                    <span className="text-[#A1A1AA] text-sm leading-relaxed">{item.text}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex-shrink-0 w-full md:w-72">
              <div className="bg-[#09090B] border border-[#27272A] rounded-2xl p-6 space-y-4">
                <p className="text-[10px] font-bold text-[#52525B] uppercase tracking-widest">Sample output — Fitness creator</p>
                <div className="space-y-2">
                  <p className="text-xs font-bold text-[#3B82F6]">1/</p>
                  <p className="text-sm text-[#E4E4E7] leading-relaxed">Nobody talks about this, but 80% of people quit their workout program in week 3 — not week 1.</p>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-bold text-[#3B82F6]">2/</p>
                  <p className="text-sm text-[#E4E4E7] leading-relaxed">Week 1 is motivation. Week 2 is habit-building. Week 3 is where the identity shift has to happen — or it doesn't.</p>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-bold text-[#3B82F6]">3/</p>
                  <p className="text-sm text-[#E4E4E7] leading-relaxed">Here's the exact mindset reframe that gets my clients past week 3 every single time...</p>
                </div>
                <p className="text-[10px] text-[#52525B] italic">Generated from a 400-word blog post draft in ~20 seconds</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── STATS / SOCIAL PROOF ─────────────────────────────────── */}
      <div className="py-20 px-6 bg-[#09090B] border-b border-[#1C1C1F]">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            {[
              { stat: content.stats_users, label: content.stats_users_label },
              { stat: content.stats_generations, label: content.stats_generations_label },
              { stat: content.stats_time_saved, label: content.stats_time_saved_label },
            ].map((s, i) => (
              <div key={i} className="flex flex-col items-center">
                <span className="text-4xl md:text-5xl font-black text-white mb-2 bg-clip-text text-transparent bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6]">
                  {s.stat}
                </span>
                <span className="text-[#71717A] text-sm font-medium uppercase tracking-widest">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── TESTIMONIALS ─────────────────────────────────────────── */}
      <div className="py-24 px-6 bg-[#111113] border-y border-[#1C1C1F]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-[10px] font-bold text-[#52525B] uppercase tracking-[0.2em] mb-4 block">WHAT CREATORS SAY</span>
            <h2 className="text-3xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
              Real Results, Real Creators
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((t, i) => (
              <div key={i} className="bg-[#18181B] border border-[#27272A] rounded-2xl p-8 flex flex-col gap-6 hover:border-[#3B82F6]/30 transition-all">
                <p className="text-[#A1A1AA] text-sm leading-relaxed flex-1">"{t.text}"</p>
                <div className="flex items-center gap-3 pt-4 border-t border-[#27272A]">
                  <div className="w-10 h-10 bg-[#3B82F6]/20 rounded-full flex items-center justify-center font-bold text-[#3B82F6] text-sm">
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-white font-bold text-sm">{t.name}</p>
                    <p className="text-[#52525B] text-xs">{t.role} · {t.platform}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── LATEST FROM BLOG ─────────────────────────────────────── */}
      {latestPosts.length > 0 && (
        <div id="blog-section" className="max-w-6xl mx-auto py-24 px-6">
          <div className="text-center mb-12">
            <span className="text-[10px] font-bold text-[#52525B] uppercase tracking-[0.2em] mb-4 block">LATEST CONTENT</span>
            <h2 className="text-3xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
              Latest from the Blog
            </h2>
            <p className="text-gray-400 mt-4">Tips and strategies to find your angle and go viral.</p>
            <Link to="/blog" className="inline-flex items-center gap-2 mt-6 text-accent font-bold hover:underline">
              View All Posts <span>→</span>
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {latestPosts.map(post => (
              <Link
                key={post.id}
                to={`/blog/${post.slug}`}
                className="group bg-card/30 border border-border/50 rounded-2xl overflow-hidden hover:border-accent/30 transition-all hover:translate-y-[-4px]"
              >
                {post.featured_image_url && (
                  <div className="aspect-video overflow-hidden">
                    <img src={post.featured_image_url} alt={post.title} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                  </div>
                )}
                <div className="p-6 h-full flex flex-col">
                  <div className="text-[10px] font-bold text-accent uppercase tracking-widest mb-3">{post.category}</div>
                  <h3 className="text-xl font-bold mb-3 group-hover:text-accent transition-colors" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{post.title}</h3>
                  <p className="text-gray-400 text-sm line-clamp-3 mb-4">{post.excerpt}</p>
                  <div className="flex items-center justify-between mt-auto pt-4 border-t border-border/10">
                    <span className="text-[10px] text-gray-500 font-bold uppercase">{post.read_time_minutes} min read</span>
                    <span className="text-xs font-bold text-white group-hover:translate-x-1 transition-transform">Read More →</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── PRICING PREVIEW (id="pricing") ───────────────────────── */}
      <div id="pricing" className="py-20 px-6 bg-[#111113] border-y border-[#1C1C1F] text-center">
        <div className="max-w-xl mx-auto">
          <span className="text-[10px] font-bold text-[#52525B] uppercase tracking-[0.2em] mb-4 block">PRICING</span>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Start Free. Upgrade When Ready.</h2>
          <p className="text-[#71717A] mb-8">5 free generations — no credit card. Starter from $12/month. Pro from $19/month.</p>
          <Link to="/pricing" className="inline-flex items-center justify-center bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold text-sm h-[48px] px-8 rounded-xl shadow-lg shadow-blue-500/20 transition-all hover:scale-105">
            See All Plans →
          </Link>
        </div>
      </div>

      {/* ── FAQ ──────────────────────────────────────────────────── */}
      <div id="faq" className="bg-[#09090B] py-24 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <span className="text-[10px] font-bold text-[#52525B] uppercase tracking-[0.2em] mb-4 block">GOT QUESTIONS?</span>
            <h2 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-400">
              {content.faq_title}
            </h2>
          </div>
          <div className="bg-card/20 backdrop-blur-md border border-border/30 rounded-2xl overflow-hidden shadow-2xl">
            {faqs.map((faq, index) => (
              <FAQItem
                key={index}
                question={faq.q}
                answer={faq.a}
                isOpen={openFAQ === index}
                onClick={() => setOpenFAQ(openFAQ === index ? null : index)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* ── BOTTOM CTA ───────────────────────────────────────────── */}
      <div className="py-24 px-6 bg-[#111113] border-t border-[#1C1C1F] text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#3B82F6]/5 to-transparent pointer-events-none"></div>
        <div className="max-w-2xl mx-auto relative z-10">
          <div className="w-16 h-16 bg-gradient-to-br from-[#3B82F6] to-purple-600 rounded-2xl flex items-center justify-center text-3xl mx-auto mb-8 shadow-xl shadow-[#3B82F6]/30">⚡</div>
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">{marketingCopy.bottom_cta_headline}</h2>
          <p className="text-[#71717A] text-lg mb-4">{marketingCopy.bottom_cta_subtext}</p>
          <p className="text-[#52525B] text-sm mb-10">Text &amp; video generation · 5 platforms · Voice learning · AI Video Studio</p>
          <Link to="/signup" className="inline-flex items-center justify-center bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold text-[16px] h-[56px] px-10 rounded-xl shadow-xl shadow-blue-500/20 transition-all hover:scale-105 active:scale-95">
            {marketingCopy.bottom_cta_button}
          </Link>
          <p className="text-[#52525B] text-xs mt-6">No credit card required · Cancel anytime · 5 free generations</p>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Landing;
