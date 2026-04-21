import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useCMS } from '../hooks/useCMS';
import { useSEO } from '../hooks/useSEO';

export default function About() {
  const { content } = useCMS('about', {
    about_badge: 'OUR STORY',
    about_headline: 'Built by a Creator, For Creators',
    about_subheadline: 'Threadangle started because I was spending 3 hours every week turning my blog posts into social content. There had to be a better way.',
    about_founder_title: 'Hi, I am the founder of Kriangle',
    about_founder_subtitle: 'Solo developer · Building in public',
    about_founder_story: 'I am a solo developer building Threadangle in public. I got tired of watching great content die because creators did not have time to repurpose it. Threadangle is the tool I wished existed — paste your content, get platform-perfect posts in 20 seconds, and spend your time creating instead of formatting.',
    about_stat_1_value: '20 seconds',
    about_stat_1_label: 'Average generation time',
    about_stat_2_value: '3 platforms',
    about_stat_2_label: 'Twitter, LinkedIn, TikTok',
    about_mission_badge: 'WHY WE EXIST',
    about_mission_title: 'Our Mission',
    about_mission_body: 'Every creator has great ideas. Not every creator has time to adapt those ideas for every platform. Threadangle exists to remove that barrier — so your ideas reach more people, on more platforms, with less effort.',
    about_values_title: 'What We Believe',
    about_values: [
      { icon: '⚡', title: 'Speed matters', body: 'Your time is the most valuable thing you have. We measure success in seconds, not minutes.' },
      { icon: '🎯', title: 'Platform context', body: 'A Twitter thread is not a LinkedIn post. Each platform has its own language and we speak all of them.' },
      { icon: '🔨', title: 'Built in public', body: 'We share our progress, our numbers, and our mistakes openly. No corporate speak. Just honest building.' }
    ],
    about_cta_title: 'Want to Try It?',
    about_cta_body: '5 free generations. No credit card. No commitment.',
    about_cta_button: 'Start Free — No Credit Card'
  });

  const { content: seo } = useCMS('seo', {
    about_meta_title: 'About — Threadangle',
    about_meta_description: 'Threadangle is built by Kriangle to help creators turn content into viral social posts at scale.'
  });
  const { content: global } = useCMS('global', {
    twitter_url: 'https://twitter.com/threadangle'
  });

  useSEO({
    title: seo.about_meta_title,
    description: seo.about_meta_description,
  });

  const values = Array.isArray(content.about_values) ? content.about_values : [];

  return (
    <div className="min-h-screen bg-[#09090B] text-white font-sans selection:bg-accent/30 selection:text-white">
      <Navbar />

      {/* ── HERO ───────────────────────────────────────────────── */}
      <div className="px-6 text-center relative overflow-hidden" style={{ paddingTop: '80px', paddingBottom: '60px' }}>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-[#3B82F6]/8 rounded-full blur-3xl pointer-events-none"></div>
        <div className="max-w-3xl mx-auto relative z-10">
          <span className="text-[10px] font-bold text-[#52525B] uppercase tracking-[0.2em] mb-6 block">{content.about_badge}</span>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-500 leading-tight">
            {content.about_headline}
          </h1>
          <p className="text-[#71717A] text-lg md:text-xl leading-relaxed max-w-2xl mx-auto">
            {content.about_subheadline}
          </p>
        </div>
      </div>

      {/* ── FOUNDER ────────────────────────────────────────────── */}
      <div className="px-6" style={{ paddingTop: '60px', paddingBottom: '60px' }}>
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-16 h-16 bg-[#3B82F6]/20 rounded-2xl flex items-center justify-center text-3xl font-bold text-[#3B82F6]">K</div>
            <div>
              <h2 className="text-2xl font-bold text-white">{content.about_founder_title}</h2>
              <p className="text-[#52525B] text-sm mt-1">{content.about_founder_subtitle}</p>
            </div>
          </div>
          <p className="text-[#A1A1AA] text-lg leading-relaxed mb-10">
            {content.about_founder_story}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
            <div className="bg-[#111113] border border-[#27272A] rounded-2xl p-8 text-center hover:border-[#3B82F6]/30 transition-all">
              <span className="text-4xl font-black text-white bg-clip-text text-transparent bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6]">{content.about_stat_1_value}</span>
              <p className="text-[#71717A] text-sm mt-2 uppercase tracking-widest font-medium">{content.about_stat_1_label}</p>
            </div>
            <div className="bg-[#111113] border border-[#27272A] rounded-2xl p-8 text-center hover:border-[#3B82F6]/30 transition-all">
              <span className="text-4xl font-black text-white bg-clip-text text-transparent bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6]">{content.about_stat_2_value}</span>
              <p className="text-[#71717A] text-sm mt-2 uppercase tracking-widest font-medium">{content.about_stat_2_label}</p>
            </div>
          </div>

          <p className="text-[#52525B] text-sm text-center">
            Building in public from day one · Follow the journey{' '}
            <a href={global.twitter_url} target="_blank" rel="noopener noreferrer" className="text-[#3B82F6] hover:underline">@threadangle</a>
          </p>
        </div>
      </div>

      {/* ── MISSION ────────────────────────────────────────────── */}
      <div style={{ background: '#111113', borderTop: '1px solid #1C1C1F', borderBottom: '1px solid #1C1C1F', padding: '80px 24px' }}>
        <div className="max-w-3xl mx-auto text-center">
          <span className="text-[10px] font-bold text-[#52525B] uppercase tracking-[0.2em] mb-6 block">{content.about_mission_badge}</span>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-8">{content.about_mission_title}</h2>
          <p className="text-[#A1A1AA] text-lg leading-relaxed">
            {content.about_mission_body}
          </p>
        </div>
      </div>

      {/* ── VALUES ─────────────────────────────────────────────── */}
      <div className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <span className="text-[10px] font-bold text-[#52525B] uppercase tracking-[0.2em] mb-4 block">PRINCIPLES</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white">{content.about_values_title}</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {values.map((v, i) => (
              <div key={i} className="bg-[#111113] border border-[#27272A] rounded-2xl hover:border-[#3B82F6]/30 transition-all" style={{ padding: '28px' }}>
                <div className="text-3xl" style={{ marginBottom: '16px' }}>{v.icon}</div>
                <h3 className="text-lg font-bold text-white" style={{ marginBottom: '12px' }}>{v.title}</h3>
                <p className="text-[#71717A]" style={{ fontSize: '14px', lineHeight: '1.7' }}>{v.body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── CTA ────────────────────────────────────────────────── */}
      <div className="py-24 px-6 bg-[#111113] border-t border-[#1C1C1F] text-center">
        <div className="max-w-xl mx-auto">
          <div className="w-14 h-14 bg-[#3B82F6] rounded-2xl flex items-center justify-center text-2xl mx-auto mb-8 shadow-xl shadow-[#3B82F6]/30">⚡</div>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">{content.about_cta_title}</h2>
          <p className="text-[#71717A] text-lg mb-10">{content.about_cta_body}</p>
          <Link
            to="/signup"
            className="inline-flex items-center justify-center bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold text-[16px] h-[52px] px-10 rounded-xl shadow-xl shadow-blue-500/20 transition-all hover:scale-105 active:scale-95"
          >
            {content.about_cta_button}
          </Link>
          <p className="text-[#52525B] text-xs mt-6">5 free generations · No credit card · Cancel anytime</p>
        </div>
      </div>

      <Footer />
    </div>
  );
}
