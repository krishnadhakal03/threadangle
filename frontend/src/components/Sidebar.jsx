import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../utils/api';
import ThreadangleLogo from './ThreadangleLogo';

function BugReportModal({ user, onClose }) {
  const [form, setForm] = useState({ category: 'UI/Display Issue', description: '', steps: '', severity: 'medium' });
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.description.trim() || form.description.trim().length < 10) {
      setError('Please describe the issue (minimum 10 characters).');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await api.submitBugReport({
        category: form.category,
        description: form.description.trim(),
        steps: form.steps.trim(),
        severity: form.severity,
        user_email: user?.email || '',
        user_plan: user?.plan || '',
      });
      setSuccess(true);
      setTimeout(onClose, 2200);
    } catch (err) {
      setError(err.message || 'Failed to submit. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#18181B] border border-[#27272A] rounded-2xl shadow-2xl w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#27272A]">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🐛</span>
            <div>
              <h2 className="text-white text-lg font-bold">Report a Bug</h2>
              <p className="text-[#71717A] text-xs mt-0.5">We'll investigate within 24 hours</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-[#71717A] hover:text-white hover:bg-[#27272A] transition-all">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {success ? (
          <div className="p-8 text-center">
            <div className="w-14 h-14 rounded-full bg-green-500/15 border border-green-500/30 flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            </div>
            <h3 className="text-white font-bold text-lg mb-1">Bug Report Submitted!</h3>
            <p className="text-[#71717A] text-sm">We'll investigate and follow up at {user?.email}.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Category */}
            <div>
              <label className="block text-xs font-bold text-[#71717A] uppercase tracking-widest mb-1.5">Category</label>
              <select
                value={form.category}
                onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-3 py-2.5 text-white text-sm focus:border-[#3B82F6] outline-none"
              >
                {['UI/Display Issue', 'Content Generation Bug', 'Scheduling Issue', 'Account/Billing', 'Performance', 'Feature Request', 'Other'].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div>
              <label className="block text-xs font-bold text-[#71717A] uppercase tracking-widest mb-1.5">Description <span className="text-red-400">*</span></label>
              <textarea
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                placeholder="Describe what happened and what you expected..."
                rows={3}
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-3 py-2.5 text-white text-sm placeholder:text-[#52525B] focus:border-[#3B82F6] outline-none resize-none"
                required
              />
            </div>

            {/* Steps */}
            <div>
              <label className="block text-xs font-bold text-[#71717A] uppercase tracking-widest mb-1.5">Steps to Reproduce <span className="text-[#52525B] font-normal normal-case">(optional)</span></label>
              <textarea
                value={form.steps}
                onChange={e => setForm(f => ({ ...f, steps: e.target.value }))}
                placeholder={"1. I went to...\n2. I clicked...\n3. The bug appeared..."}
                rows={3}
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-3 py-2.5 text-white text-sm placeholder:text-[#52525B] focus:border-[#3B82F6] outline-none resize-none"
              />
            </div>

            {/* Severity */}
            <div>
              <label className="block text-xs font-bold text-[#71717A] uppercase tracking-widest mb-2">Severity</label>
              <div className="flex gap-2">
                {[
                  { val: 'low', label: 'Low', desc: 'Minor annoyance', color: 'text-yellow-400 border-yellow-500/40 bg-yellow-500/10' },
                  { val: 'medium', label: 'Medium', desc: 'Affects workflow', color: 'text-orange-400 border-orange-500/40 bg-orange-500/10' },
                  { val: 'high', label: 'High', desc: "Can't use app", color: 'text-red-400 border-red-500/40 bg-red-500/10' },
                ].map(s => (
                  <button
                    key={s.val}
                    type="button"
                    onClick={() => setForm(f => ({ ...f, severity: s.val }))}
                    className={`flex-1 p-2.5 rounded-xl border-2 text-center transition-all ${form.severity === s.val ? s.color + ' border-opacity-100' : 'border-[#27272A] text-[#71717A] hover:border-[#3F3F46]'}`}
                  >
                    <div className="text-xs font-bold">{s.label}</div>
                    <div className="text-[10px] opacity-70 mt-0.5">{s.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {error && <p className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 bg-[#3B82F6] hover:bg-[#2563EB] disabled:opacity-50 text-white font-bold rounded-xl transition-all text-sm"
            >
              {submitting ? 'Submitting...' : 'Submit Bug Report'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default function Sidebar({ activeTab, setActiveTab }) {
  const { user, logout } = useAuth();
  const [showBugModal, setShowBugModal] = useState(false);

  const menuItems = [
    { id: 'dashboard', label: 'Generate', icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
    )},
    { id: 'ai-video', label: 'Video Studio', icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14m-9 4h8a2 2 0 002-2V8a2 2 0 00-2-2H6a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
    )},
    { id: 'history', label: 'History', icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
    )},
    { id: 'calendar', label: 'Calendar', icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
    )},
    ...(user?.plan === 'free' ? [{ id: 'upgrade', label: 'Upgrade', icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>
    )}] : []),
    { id: 'settings', label: 'Settings', icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
    )},
  ];

  const planLimit = user?.plan === 'free' ? 5 : user?.plan === 'solo' ? 30 : user?.plan === 'founder' ? 100 : 9999;
  const usagePct = Math.min(((user?.usage_count ?? 0) / planLimit) * 100, 100);
  const displayLimit = planLimit === 9999 ? '\u221e' : planLimit;

  return (
    <aside className="w-64 bg-[#18181B] border-r border-[#27272A] flex flex-col h-screen sticky top-0">
      <div className="p-5 border-b border-[#27272A]">
        <ThreadangleLogo size={32} showText={true} textSize={16} />
      </div>

      <nav className="flex-1 p-3 space-y-1 mt-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium text-sm ${
              item.id === 'upgrade'
                ? activeTab === item.id
                  ? 'text-amber-400 bg-amber-500/10'
                  : 'text-amber-400 hover:bg-amber-500/10'
                : activeTab === item.id
                  ? 'bg-[#3B82F6] text-white shadow-lg shadow-[#3B82F6]/20'
                  : 'text-[#71717A] hover:bg-[#27272A] hover:text-white'
            }`}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-[#27272A]">
        {/* Usage / Plan */}
        <div className="bg-[#09090B] p-4 rounded-xl border border-[#27272A] mb-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold text-[#71717A] uppercase tracking-wider">
              {user?.plan === 'free' ? 'Free Plan' : 'Usage This Month'}
            </span>
            <div className="flex items-center gap-1.5">
              {user?.plan === 'solo' && (
                <span className="px-1.5 py-0.5 bg-blue-500/10 border border-blue-500/30 rounded text-[9px] font-bold text-blue-400">⚡ SOLO</span>
              )}
              {user?.plan === 'founder' && (
                <span className="px-1.5 py-0.5 bg-purple-500/10 border border-purple-500/30 rounded text-[9px] font-bold text-purple-400">⭐ FOUNDER</span>
              )}
              <span className="text-[10px] font-bold text-[#3B82F6] uppercase">
                {user?.usage_count ?? 0}/{displayLimit}
              </span>
            </div>
          </div>
          <div className="w-full bg-[#27272A] rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                usagePct >= 100 ? 'bg-red-500'
                : user?.plan === 'founder' ? 'bg-gradient-to-r from-purple-500 to-pink-500'
                : 'bg-[#3B82F6]'
              }`}
              style={{ width: `${usagePct}%` }}
            />
          </div>
          {user?.plan === 'solo' && (
            <div className="mt-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <div className="text-xs font-medium text-blue-400">SOLO PLAN</div>
              <div className="text-xs text-gray-400 mt-0.5">30 generations/month</div>
            </div>
          )}
          {user?.plan === 'founder' && (
            <div className="mt-2 px-3 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-lg">
              <div className="text-xs font-medium text-purple-400">⭐ FOUNDER PLAN</div>
              <div className="text-xs text-gray-400 mt-0.5">100 generations/month</div>
            </div>
          )}
          {user?.plan === 'free' && (
            <button
              onClick={() => setActiveTab('upgrade')}
              className="mt-3 w-full py-2 text-xs font-bold text-[#3B82F6] border border-[#3B82F6]/30 rounded-lg hover:bg-[#3B82F6]/10 transition-all"
            >
              Upgrade Plan →
            </button>
          )}
        </div>

        {/* Voice Learning Status */}
        {user?.voice_learned ? (
          <div className="px-4 pb-3">
            <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-xl">
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-sm">🎤</span>
                <span className="text-[10px] font-bold text-green-400 uppercase tracking-wider">Voice Profile Active</span>
                <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse ml-auto" />
              </div>
              {user?.voice_samples_submitted ? (
                <p className="text-[11px] text-green-300/80 leading-relaxed">Trained on your writing samples</p>
              ) : (
                <p className="text-[11px] text-green-300/80 leading-relaxed">Learned from your generations</p>
              )}
              {user?.niche_tags && (() => {
                try {
                  const tags = JSON.parse(user.niche_tags);
                  return tags.length > 0 ? (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {tags.slice(0, 3).map((t, i) => (
                        <span key={i} className="text-[9px] px-1.5 py-0.5 bg-green-500/20 text-green-300 rounded-full font-medium">{t.split(' ').slice(-1)[0]}</span>
                      ))}
                      {tags.length > 3 && <span className="text-[9px] text-green-400/60">+{tags.length - 3}</span>}
                    </div>
                  ) : null;
                } catch { return null; }
              })()}
            </div>
          </div>
        ) : (user?.successful_generations_count ?? 0) > 0 ? (
          <div className="px-4 pb-3">
            <div className="p-3 bg-[#18181B] border border-[#27272A] rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[12px] font-semibold text-gray-300">🎤 Voice Learning</span>
                <span className="text-[11px] font-bold text-blue-400">
                  {Math.min(user.successful_generations_count, 3)}/3
                </span>
              </div>
              <div className="w-full bg-[#27272A] rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-purple-500 to-blue-500 h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min((user.successful_generations_count / 3) * 100, 100)}%` }}
                />
              </div>
              <p className="text-[11px] text-gray-400 mt-2 leading-relaxed">
                {Math.max(3 - user.successful_generations_count, 0)} more generation{Math.max(3 - user.successful_generations_count, 0) !== 1 ? 's' : ''} until your AI sounds like you.
              </p>
              <button
                onClick={() => setActiveTab('settings')}
                className="mt-2 text-[10px] text-purple-400 hover:text-purple-300 underline underline-offset-2"
              >
                ⚡ Fast-track: add writing samples →
              </button>
            </div>
          </div>
        ) : null}

        {/* User info */}
        <div className="flex items-center gap-3 px-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-[#3B82F6] flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
            {user?.name ? user.name[0].toUpperCase() : user?.email ? user.email[0].toUpperCase() : '?'}
          </div>
          <div className="min-w-0">
            <p className="text-white text-xs font-semibold truncate">{user?.name || 'User'}</p>
            <p className="text-[#71717A] text-[10px] truncate">{user?.email}</p>
          </div>
        </div>

        <button
          onClick={() => setShowBugModal(true)}
          className="w-full flex items-center gap-2 px-4 py-2.5 text-[#71717A] hover:text-orange-400 hover:bg-orange-500/5 rounded-xl transition-all text-sm font-medium"
        >
          <span className="text-base">🐛</span>
          Report Bug
        </button>

        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-4 py-2.5 text-[#71717A] hover:text-red-400 hover:bg-red-500/5 rounded-xl transition-all text-sm font-medium"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
          Sign Out
        </button>
      </div>

      {showBugModal && createPortal(
        <BugReportModal user={user} onClose={() => setShowBugModal(false)} />,
        document.body
      )}
    </aside>
  );
}
