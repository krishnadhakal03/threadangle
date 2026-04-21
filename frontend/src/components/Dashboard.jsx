import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import { loadStripe } from '@stripe/stripe-js';
import { api } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { useDialog } from '../context/DialogContext';
import HelpChatbot from './HelpChatbot';
import SocialPlatformIcon from './SocialPlatformIcon';
import TimelinePreview from './TimelinePreview';
import VideoEditor from './VideoEditor';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

function StripeCheckoutModal({ clientSecret, onClose }) {
  const [isLoading, setIsLoading] = useState(true);
  const checkoutRef = useRef(null);

  useEffect(() => {
    if (!clientSecret) return;
    let destroyed = false;

    (async () => {
      try {
        const stripe = await stripePromise;
        if (destroyed) return;
        const checkout = await stripe.initEmbeddedCheckout({ clientSecret });
        if (destroyed) { checkout.destroy(); return; }
        checkoutRef.current = checkout;
        checkout.mount('#stripe-checkout-container');
        setIsLoading(false);
      } catch (err) {
        console.error('Stripe checkout error:', err);
      }
    })();

    return () => {
      destroyed = true;
      if (checkoutRef.current) {
        checkoutRef.current.destroy();
        checkoutRef.current = null;
      }
    };
  }, [clientSecret]);

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.85)',
      backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9998, padding: '16px',
    }}>
      <div style={{
        background: '#0f0f11', borderRadius: '16px',
        maxWidth: '640px', width: '100%',
        maxHeight: '90vh', overflowY: 'auto',
        position: 'relative',
        border: '1px solid #27272A',
        boxShadow: '0 24px 64px rgba(0,0,0,0.8)',
      }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: '16px', right: '16px',
            background: '#27272A', border: 'none', borderRadius: '50%',
            width: '32px', height: '32px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', color: '#A1A1AA', zIndex: 10,
          }}
          aria-label="Close checkout"
        >
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div style={{ padding: '24px 24px 20px', borderBottom: '1px solid #1a1a1f' }}>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#FAFAFA' }}>
            Complete Your Subscription
          </div>
          <div style={{ fontSize: '13px', color: '#71717A', marginTop: '4px' }}>
            Secure checkout powered by Stripe
          </div>
        </div>

        {isLoading && (
          <div style={{
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            padding: '48px 24px',
          }}>
            <div style={{
              width: '40px', height: '40px',
              border: '3px solid #27272A', borderTopColor: '#3B82F6',
              borderRadius: '50%', animation: 'spin 0.8s linear infinite',
              marginBottom: '16px',
            }} />
            <div style={{ color: '#71717A', fontSize: '14px' }}>Loading secure checkout...</div>
          </div>
        )}

        <div id="stripe-checkout-container" />
      </div>
    </div>
  );
}

const PLATFORM_LABELS = { twitter: 'Twitter / X', linkedin: 'LinkedIn', tiktok: 'TikTok', reels: 'Instagram Reels', shorts: 'YouTube Shorts' };
const PLATFORM_ICONS = {
  twitter: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.741l7.73-8.835L1.254 2.25H8.08l4.261 5.632 5.903-5.632Zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>
  ),
  linkedin: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" /></svg>
  ),
  tiktok: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.27 8.27 0 004.84 1.55V6.79a4.85 4.85 0 01-1.07-.1z" /></svg>
  ),
  reels: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
  ),
  shorts: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
  ),
};

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };
  return (
    <button
      onClick={handleCopy}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
        copied ? 'bg-green-500/20 text-green-400' : 'bg-[#27272A] text-[#A1A1AA] hover:text-white hover:bg-[#3F3F46]'
      }`}
    >
      {copied ? (
        <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>Copied!</>
      ) : (
        <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>Copy</>
      )}
    </button>
  );
}

// Normalize raw output value (may be string or array) to a plain string
function normalizeContent(raw) {
  if (!raw) return '';
  if (Array.isArray(raw)) return raw.map(item => (typeof item === 'string' ? item : item?.text || '')).join('\n\n');
  return String(raw);
}

function EditableOutput({ platform, content, generationId }) {
  const { confirm: confirmDialog } = useDialog();
  const initial = normalizeContent(content);
  const [text, setText] = useState(initial);
  const [savingState, setSavingState] = useState('idle'); // idle | saving | saved
  const [copied, setCopied] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const histRef = useRef({ stack: [initial], idx: 0 });
  const saveTimeoutRef = useRef(null);
  const textareaRef = useRef(null);
  const prevKeyRef = useRef(`${generationId}-${platform}`);

  // Reset when a new generation arrives (generationId or content changes)
  useEffect(() => {
    const key = `${generationId}-${platform}`;
    if (prevKeyRef.current !== key) {
      prevKeyRef.current = key;
      const fresh = normalizeContent(content);
      setText(fresh);
      histRef.current = { stack: [fresh], idx: 0 };
      setCanUndo(false);
      setCanRedo(false);
      setSavingState('idle');
    }
  }, [generationId, platform, content]);

  // Auto-resize textarea to fit content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [text]);

  const getCharInfo = () => {
    if (platform === 'twitter') {
      const tweets = text.split(/\n\n+/).filter(t => t.trim().length > 0);
      const maxLen = tweets.length ? Math.max(...tweets.map(t => t.trim().length)) : 0;
      return { count: maxLen, limit: 280, note: 'longest tweet' };
    }
    if (platform === 'linkedin') return { count: text.length, limit: 3000, note: '' };
    if (platform === 'tiktok') return { count: text.length, limit: 2200, note: '' };
    if (platform === 'reels_title') return { count: text.length, limit: 150, note: 'title chars' };
    if (platform === 'reels_description') return { count: text.length, limit: 2200, note: 'caption chars' };
    if (platform === 'reels_hashtags') return { count: text.split(' ').filter(h => h.startsWith('#')).length, limit: 30, note: 'hashtags' };
    if (platform === 'shorts_title') return { count: text.length, limit: 60, note: 'title chars' };
    if (platform === 'shorts_description') return { count: text.length, limit: 5000, note: 'desc chars' };
    if (platform === 'shorts_tags') return { count: text.split(',').filter(t => t.trim()).length, limit: 15, note: 'tags' };
    return { count: text.length, limit: 0, note: '' };
  };

  const { count, limit, note } = getCharInfo();
  const pct = limit ? (count / limit) * 100 : 0;
  const isOverLimit = pct >= 100;
  const isNearLimit = pct >= 85 && !isOverLimit;
  const countColor = isOverLimit ? '#f87171' : isNearLimit ? '#fbbf24' : '#52525B';

  const doSave = async (val) => {
    if (!generationId) return;
    setSavingState('saving');
    try {
      await api.saveEdit(generationId, platform, val);
      setSavingState('saved');
      setTimeout(() => setSavingState(s => (s === 'saved' ? 'idle' : s)), 2000);
    } catch {
      setSavingState('idle');
    }
  };

  const pushToHistory = (val) => {
    const { stack, idx } = histRef.current;
    const newStack = [...stack.slice(0, idx + 1), val].slice(-50);
    histRef.current = { stack: newStack, idx: newStack.length - 1 };
    setCanUndo(newStack.length > 1);
    setCanRedo(false);
  };

  const handleChange = (e) => {
    const val = e.target.value;
    setText(val);
    setSavingState('saving');
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => {
      pushToHistory(val);
      doSave(val);
    }, 1000);
  };

  const handleUndo = () => {
    const { stack, idx } = histRef.current;
    if (idx > 0) {
      const newIdx = idx - 1;
      histRef.current.idx = newIdx;
      const val = stack[newIdx];
      setText(val);
      setCanUndo(newIdx > 0);
      setCanRedo(true);
      doSave(val);
    }
  };

  const handleRedo = () => {
    const { stack, idx } = histRef.current;
    if (idx < stack.length - 1) {
      const newIdx = idx + 1;
      histRef.current.idx = newIdx;
      const val = stack[newIdx];
      setText(val);
      setCanUndo(true);
      setCanRedo(newIdx < stack.length - 1);
      doSave(val);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const handleReset = async () => {
    const confirmed = await confirmDialog({
      title: 'Reset Edited Content?',
      message: 'Reset to original AI content? Your edits will be lost.',
      confirmText: 'Reset Content',
      cancelText: 'Keep Edits',
      tone: 'danger',
    });
    if (!confirmed) return;

    const original = normalizeContent(content);
    setText(original);
    pushToHistory(original);
    doSave(original);
  };

  const hasBeenEdited = text !== initial;

  return (
    <div className="space-y-2">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {/* Undo */}
          <button
            onClick={handleUndo}
            disabled={!canUndo}
            title="Undo (Ctrl+Z)"
            className="p-1.5 rounded-lg bg-[#27272A] text-[#71717A] hover:text-white hover:bg-[#3F3F46] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
          </button>
          {/* Redo */}
          <button
            onClick={handleRedo}
            disabled={!canRedo}
            title="Redo (Ctrl+Shift+Z)"
            className="p-1.5 rounded-lg bg-[#27272A] text-[#71717A] hover:text-white hover:bg-[#3F3F46] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10h-10a8 8 0 00-8 8v2m18-10l-6 6m6-6l-6-6" />
            </svg>
          </button>
          {/* Reset (only when edited) */}
          {hasBeenEdited && (
            <button
              onClick={handleReset}
              title="Reset to original AI content"
              className="flex items-center gap-1 px-2 py-1.5 rounded-lg bg-[#27272A] text-[#71717A] hover:text-white text-[11px] font-medium transition-all"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Reset
            </button>
          )}
          {/* Save status */}
          {savingState === 'saving' && <span className="text-[11px] text-[#71717A] animate-pulse ml-1">Saving…</span>}
          {savingState === 'saved' && <span className="text-[11px] text-green-400 ml-1">✓ Saved</span>}
        </div>
        {/* Char counter */}
        {limit > 0 && (
          <div className="flex items-center gap-1.5">
            {note && <span className="text-[10px] text-[#3F3F46]">{note}</span>}
            <span className="text-[11px] font-mono" style={{ color: countColor }}>
              {count}/{limit}
            </span>
            {isOverLimit && <span className="text-[10px] text-red-400">⚠ over</span>}
          </div>
        )}
      </div>

      {/* Editable textarea */}
      <div className={`relative border rounded-xl transition-colors ${isOverLimit ? 'border-red-500/40' : 'border-[#27272A] focus-within:border-[#3B82F6]/60'}`}>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          spellCheck
          className="w-full bg-[#09090B] text-[#E4E4E7] text-sm leading-relaxed p-4 outline-none resize-none rounded-xl"
          style={{ minHeight: '120px', display: 'block' }}
        />
      </div>

      {/* Copy button */}
      <div className="flex justify-end">
        <button
          onClick={handleCopy}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            copied ? 'bg-green-500/20 text-green-400' : 'bg-[#27272A] text-[#A1A1AA] hover:text-white hover:bg-[#3F3F46]'
          }`}
        >
          {copied ? (
            <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>Copied!</>
          ) : (
            <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>Copy</>
          )}
        </button>
      </div>
    </div>
  );
}

function replaceHookInContent(content, newHook, platform) {
  if (!content) return content;
  if (platform === 'twitter') {
    const replaced = content.replace(/^(1\/\s*).+?(?=\n\n2\/|\n2\/)/s, `$1${newHook}`);
    return replaced !== content ? replaced : `1/ ${newHook}\n\n${content}`;
  }
  if (platform === 'linkedin') {
    const parts = content.split('\n\n');
    return [newHook, ...parts.slice(1)].join('\n\n');
  }
  if (platform === 'tiktok') {
    const replaced = content.replace(
      /(🎬[^\n]*\n).+?(\n\n(?:📱|💡|✨))/s,
      `$1${newHook}$2`
    );
    return replaced !== content ? replaced : content;
  }
  return content;
}

const HOOK_TYPES = [
  { emoji: '🔍', label: 'Curiosity',     color: '#3B82F6' },
  { emoji: '⚡', label: 'Controversial', color: '#EF4444' },
  { emoji: '📊', label: 'Statistics',   color: '#10B981' },
  { emoji: '📖', label: 'Story',        color: '#8B5CF6' },
  { emoji: '🎯', label: 'Promise',      color: '#F59E0B' },
];

function HookVariationsPanel({ variations, onUseHook }) {
  const [expanded, setExpanded] = useState(true);
  if (!variations || variations.length === 0) return null;
  return (
    <div className="mb-4 border border-[#3B82F6]/30 bg-[#3B82F6]/5 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-[#3B82F6]/10 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-base">🔥</span>
          <span className="text-sm font-semibold text-white">5 Hook Variations — swap the opening line</span>
          <span className="text-[10px] text-[#3B82F6] bg-[#3B82F6]/20 px-1.5 py-0.5 rounded-full font-bold">A/B test</span>
        </div>
        <svg className={`w-4 h-4 text-[#71717A] transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {expanded && (
        <div className="border-t border-[#27272A] p-4 space-y-2">
          {variations.map((hook, i) => {
            const type = HOOK_TYPES[i] || HOOK_TYPES[0];
            return (
              <div key={i} className="flex items-start gap-3 p-3 bg-[#09090B] border border-[#27272A] hover:border-[#3F3F46] rounded-lg transition-colors">
                <div className="flex-shrink-0 flex items-center gap-1 pt-0.5" style={{ minWidth: '92px' }}>
                  <span className="text-sm">{type.emoji}</span>
                  <span className="text-[10px] font-bold uppercase tracking-wide" style={{ color: type.color }}>{type.label}</span>
                </div>
                <p className="flex-1 text-sm text-[#A1A1AA] leading-relaxed">{hook}</p>
                <button
                  onClick={() => onUseHook(hook)}
                  className="flex-shrink-0 px-3 py-1 text-xs font-semibold bg-[#27272A] text-[#71717A] hover:bg-[#3B82F6] hover:text-white rounded-lg transition-all whitespace-nowrap"
                >
                  Use This
                </button>
              </div>
            );
          })}
          <p className="text-[11px] text-[#52525B] pt-1">💡 Click “Use This” to swap the hook and autosave the edit</p>
        </div>
      )}
    </div>
  );
}

function ReelsMetadataOutput({ meta, generationId, hookVariations, onHookSelect, hookTitleVersion = 0 }) {
  const [copiedAll, setCopiedAll] = useState(false);
  const copyAll = async () => {
    try {
      await navigator.clipboard.writeText(`${meta.title}\n\n${meta.description}\n\n${meta.hashtags}`);
      setCopiedAll(true);
      setTimeout(() => setCopiedAll(false), 2000);
    } catch {}
  };
  const allTags = meta.hashtags ? meta.hashtags.split(' ').filter(h => h.startsWith('#')) : [];
  const previewTags = allTags.slice(0, 10);
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">📱 Title</label>
        {hookVariations?.length > 0 && (
          <HookVariationsPanel variations={hookVariations} onUseHook={(hook) => onHookSelect('reels', hook)} />
        )}
        <EditableOutput key={`${generationId}-reels_title-${hookTitleVersion}`} platform="reels_title" content={meta.title} generationId={generationId} />
      </div>
      <div>
        <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">📝 Description / Caption</label>
        <EditableOutput platform="reels_description" content={meta.description} generationId={generationId} />
      </div>
      <div>
        <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">🏷️ Hashtags ({allTags.length}/30)</label>
        <EditableOutput platform="reels_hashtags" content={meta.hashtags} generationId={generationId} />
        {previewTags.length > 0 && (
          <div className="mt-3 p-3 bg-[#09090B] border border-[#27272A] rounded-xl">
            <p className="text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Preview</p>
            <div className="flex flex-wrap gap-1.5">
              {previewTags.map((tag, i) => (
                <span key={i} className="text-xs px-2 py-0.5 bg-pink-500/10 text-pink-400 rounded-md">{tag}</span>
              ))}
              {allTags.length > 10 && <span className="text-xs text-[#71717A]">+{allTags.length - 10} more</span>}
            </div>
          </div>
        )}
      </div>
      <button
        onClick={copyAll}
        className={`w-full flex items-center justify-center gap-2 px-6 py-3 font-semibold text-sm rounded-xl transition-all ${
          copiedAll ? 'bg-green-500/20 text-green-400' : 'bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 text-white'
        }`}
      >
        {copiedAll
          ? <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>Copied!</>
          : <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>Copy All Reels Metadata</>
        }
      </button>
      <div className="p-4 bg-pink-500/5 border border-pink-500/20 rounded-xl">
        <div className="flex items-start gap-3">
          <span className="text-xl">💡</span>
          <div>
            <p className="text-sm font-semibold text-pink-400 mb-1">Instagram Reels Pro Tip</p>
            <p className="text-xs text-[#71717A] leading-relaxed">Post when your audience is most active (check Instagram Insights). Use all 30 hashtags. Pin a top comment with extra hashtags. Engage with comments in the first hour for better reach.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function ShortsMetadataOutput({ meta, generationId, hookVariations, onHookSelect, hookTitleVersion = 0 }) {
  const [copiedAll, setCopiedAll] = useState(false);
  const copyAll = async () => {
    try {
      await navigator.clipboard.writeText(`Title: ${meta.title}\n\nDescription:\n${meta.description}\n\nTags:\n${meta.tags}`);
      setCopiedAll(true);
      setTimeout(() => setCopiedAll(false), 2000);
    } catch {}
  };
  const tagList = meta.tags ? meta.tags.split(',').map(t => t.trim()).filter(Boolean) : [];
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">
          🎬 Title{' '}
          <span className={(meta.title || '').length > 60 ? 'text-red-400' : 'text-[#52525B]'}>
            ({(meta.title || '').length}/60 chars)
          </span>
        </label>
        {hookVariations?.length > 0 && (
          <HookVariationsPanel variations={hookVariations} onUseHook={(hook) => onHookSelect('shorts', hook)} />
        )}
        <EditableOutput key={`${generationId}-shorts_title-${hookTitleVersion}`} platform="shorts_title" content={meta.title} generationId={generationId} />
        {(meta.title || '').length > 60 && (
          <p className="text-xs text-red-400 mt-1">⚠️ Title will be truncated in YouTube search results</p>
        )}
      </div>
      <div>
        <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">📝 Description</label>
        <EditableOutput platform="shorts_description" content={meta.description} generationId={generationId} />
      </div>
      <div>
        <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">🏷️ Tags / Keywords ({tagList.length} tags)</label>
        <EditableOutput platform="shorts_tags" content={meta.tags} generationId={generationId} />
        {tagList.length > 0 && (
          <div className="mt-3 p-3 bg-[#09090B] border border-[#27272A] rounded-xl">
            <p className="text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Tag Preview</p>
            <div className="flex flex-wrap gap-1.5">
              {tagList.map((tag, i) => (
                <span key={i} className="text-xs px-2 py-0.5 bg-red-500/10 text-red-400 rounded-md">{tag}</span>
              ))}
            </div>
          </div>
        )}
      </div>
      <button
        onClick={copyAll}
        className={`w-full flex items-center justify-center gap-2 px-6 py-3 font-semibold text-sm rounded-xl transition-all ${
          copiedAll ? 'bg-green-500/20 text-green-400' : 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white'
        }`}
      >
        {copiedAll
          ? <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>Copied!</>
          : <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>Copy All Shorts Metadata</>
        }
      </button>
      <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-xl">
        <div className="flex items-start gap-3">
          <span className="text-xl">💡</span>
          <div>
            <p className="text-sm font-semibold text-red-400 mb-1">YouTube Shorts SEO Tip</p>
            <p className="text-xs text-[#71717A] leading-relaxed">Front-load keywords in title and description. YouTube is a search engine — optimize for searchability. Add timestamps in description. Link to a related long-form video if you have one.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function secondsToTimestamp(secondsValue) {
  const total = Math.max(0, Number(secondsValue) || 0);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = Math.floor(total % 60);
  if (hours > 0) return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  return `${minutes}:${String(seconds).padStart(2, '0')}`;
}

function timestampToSeconds(value) {
  const raw = String(value || '').trim();
  if (!raw) return 0;
  const parts = raw.split(':').map((p) => Number(p));
  if (parts.some((p) => Number.isNaN(p))) return 0;
  if (parts.length === 2) return Math.max(0, parts[0] * 60 + parts[1]);
  if (parts.length === 3) return Math.max(0, parts[0] * 3600 + parts[1] * 60 + parts[2]);
  return 0;
}

function createEmptyClip(index = 1) {
  const start = (index - 1) * 5;
  const end = start + 5;
  return {
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    start: secondsToTimestamp(start),
    end: secondsToTimestamp(end),
    text: '',
    url: '',
  };
}

function buildScriptFromClips(clips = []) {
  if (!Array.isArray(clips) || clips.length === 0) return '';
  return clips.map((clip, index) => {
    const startSec = timestampToSeconds(clip.start);
    const endSec = timestampToSeconds(clip.end);
    const duration = Math.max(0, endSec - startSec);
    const notes = String(clip.text || '').trim();
    const url = String(clip.url || '').trim();
    const body = [notes, url ? `URL: ${url}` : ''].filter(Boolean).join(' | ');
    return `Clip ${index + 1} · ${clip.start || '0:00'}–${clip.end || '0:05'} (${duration} sec)\n${body || 'Describe this scene...'}`;
  }).join('\n\n');
}

// ── CRITICAL FIX: Separate render script from preview script ──────────────
// composeScriptFromParts: PLAIN text for TTS/captions/render (NO labels)
function composeScriptFromParts(hook = '', body = '', cta = '') {
  const safeHook = String(hook || '').trim();
  const safeBody = String(body || '').trim();
  const safeCta = String(cta || '').trim();

  // Plain text join for TTS, captions, render - NO LABELS
  const parts = [];
  if (safeHook) parts.push(safeHook);
  if (safeBody) parts.push(safeBody);
  if (safeCta) parts.push(safeCta);
  return parts.join(' ').trim();  // Space-joined, clean text
}

// composeScriptPreview: Readable preview with labels (UI display ONLY)
function composeScriptPreview(hook = '', body = '', cta = '') {
  const safeHook = String(hook || '').trim();
  const safeBody = String(body || '').trim();
  const safeCta = String(cta || '').trim();

  // Labeled preview for visual display in UI
  const parts = [];
  if (safeHook) parts.push(`Hook: ${safeHook}`);
  if (safeBody) parts.push(`Body: ${safeBody}`);
  if (safeCta) parts.push(`CTA: ${safeCta}`);
  return parts.join('\n\n').trim();
}

function createScriptState(hook = '', body = '', cta = '', fullScript = '') {
  const safeHook = String(hook || '').trim();
  const safeBody = String(body || '').trim();
  const safeCta = String(cta || '').trim();
  // Store clean full_script (no labels) for API/TTS
  const safeFullScript = String(fullScript || composeScriptFromParts(safeHook, safeBody, safeCta)).trim();
  return {
    hook: safeHook,
    body: safeBody,
    cta: safeCta,
    full_script: safeFullScript,  // CLEAN - no "Hook:", "Body:", "CTA:" labels
  };
}

function getScriptPreviewText(hook = '', body = '', cta = '') {
  // Use labeled preview for UI display
  const composed = composeScriptPreview(hook, body, cta);
  return composed || 'Start writing Hook, Body, and CTA to generate the full script preview.';
}

function parseClipsFromScript(script = '') {
  const text = String(script || '');
  const headerPattern = /^\s*Clip\s*(\d+)\s*[·\-–]\s*([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?)\s*[\-–]\s*([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?)\s*(?:\(([^)]*)\))?\s*$/gim;
  const matches = [...text.matchAll(headerPattern)];
  if (matches.length === 0) return [];

  return matches.map((match, idx) => {
    const blockStart = match.index + match[0].length;
    const blockEnd = idx + 1 < matches.length ? matches[idx + 1].index : text.length;
    const block = text.slice(blockStart, blockEnd).trim();
    const urlMatch = block.match(/https?:\/\/\S+/i);
    const url = urlMatch ? urlMatch[0].replace(/[),.;!?]+$/, '') : '';
    const cleanText = block
      .replace(/https?:\/\/\S+/gi, '')
      .replace(/\bURL\s*:\s*/gi, '')
      .replace(/\|\s*\|/g, '|')
      .trim()
      .replace(/^\|\s*/, '')
      .replace(/\s*\|$/, '');

    return {
      id: `${Date.now()}_${idx}_${Math.random().toString(36).slice(2, 8)}`,
      start: match[2],
      end: match[3],
      text: cleanText,
      url,
    };
  });
}

function AIVideoModal({
  open,
  onClose,
  onGeneratePlan,
  onGenerateVideo,
  onGeneratePreview,
  onClearPreview,
  onStartFresh,
  loading,
  planning,
  form,
  setForm,
  scriptState,
  onScriptStateChange,
  scriptModified,
  error,
  plan,
  planError,
  preview,
  previewScenes,
  setPreviewScenes,
  characterPresets,
  videoMode,
  onRegeneratePlanFromEdits,
}) {
  const { confirm: confirmDialog } = useDialog();
  const videoStyleOptions = [
    { value: 'stock', label: 'Stock Footage' },
    { value: 'ai', label: 'AI Animation (RunwayML)' },
    { value: 'auto', label: 'Hybrid (AI + Stock)' },
  ];

  const [metaTab, setMetaTab] = useState('youtube_shorts');
  const [inputMode, setInputMode] = useState('script');
  const [clipRows, setClipRows] = useState([createEmptyClip(1)]);
  const [showStartFreshModal, setShowStartFreshModal] = useState(false);

  // ── Step navigation ────────────────────────────────────────────────────
  // activeStep controls which step is DISPLAYED (1/2/3).
  // Data availability controls which steps are REACHABLE.
  // Steps can be visited freely without clearing data.
  const [activeStep, setActiveStep] = useState(() => {
    if (preview && previewScenes?.length > 0) return 3;
    if (plan) return 2;
    return 1;
  });

  // Restore correct step every time the modal opens (or resumes with data)
  useEffect(() => {
    if (!open) return;
    setActiveStep(() => {
      if (preview && previewScenes?.length > 0) return 3;
      if (plan) return 2;
      return 1;
    });
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-advance to step 2 the moment a plan is freshly generated
  useEffect(() => {
    if (!open || !plan) return;
    setActiveStep(prev => (prev < 2 ? 2 : prev));
  }, [plan]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-advance to step 3 the moment a storyboard arrives
  useEffect(() => {
    if (!open || !preview || !previewScenes?.length) return;
    setActiveStep(3);
  }, [preview]); // eslint-disable-line react-hooks/exhaustive-deps
  // ──────────────────────────────────────────────────────────────────────

  useEffect(() => {
    if (!open) return;
    const parsed = parseClipsFromScript(form?.script || '');
    if (parsed.length > 0) {
      setClipRows(parsed);
      setInputMode('clips');
    } else {
      setClipRows([createEmptyClip(1)]);
      setInputMode('script');
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const currentMeta = plan?.platform_meta?.[metaTab] || { title: '', description: '', hashtags: '' };
  const editableHook = scriptState?.hook || '';
  const editableBody = scriptState?.body || '';
  const editableCta = scriptState?.cta || '';
  // For display: use labeled preview; for API: use clean full_script from state
  const editableScriptPreview = composeScriptPreview(editableHook, editableBody, editableCta);
  const editableScript = scriptState?.full_script || composeScriptFromParts(editableHook, editableBody, editableCta);
  // activeStep drives display; stepState alias kept for layout classes
  const stepState = activeStep;
  const previewCredits = preview?.estimated_cost?.credits ?? null;
  const sceneCount = Array.isArray(plan?.scenes) ? plan.scenes.length : 0;
  // gen4.5 = 12 credits/sec; assume 5s per scene (60 credits each)
  const fallbackCredits = (form.scene_mode === 'stock')
    ? 0
    : sceneCount > 0 ? sceneCount * 60 : 0;
  // Use null-check not || so that a real 0 from backend is respected
  const displayedCredits = previewCredits !== null ? previewCredits : fallbackCredits;
  const copyMeta = async () => {
    const text = `Title: ${currentMeta.title || ''}\n\nDescription:\n${currentMeta.description || ''}\n\nHashtags:\n${currentMeta.hashtags || ''}`;
    try { await navigator.clipboard.writeText(text); } catch {}
  };

  return (
    <div className="fixed inset-0 z-[10000] bg-[#06070A]">
      <div className="h-full w-full flex flex-col bg-[#0b0d12]">
        <div className="sticky top-0 z-20 border-b border-[#1f2430] bg-[#0b0d12]/95 backdrop-blur px-6 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-2xl font-bold text-white">Video Studio Workspace</div>
              <div className="text-xs text-[#8B97B3] mt-1">Full-screen storyboard workflow for plan, preview, and generation.</div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {(plan || preview) && onStartFresh && (
                <button
                  onClick={() => setShowStartFreshModal(true)}
                  className="px-3 py-1.5 rounded-lg border border-[#3F3F46] text-[#8B97B3] hover:text-white hover:border-[#52525B] text-xs font-semibold transition-colors"
                  title="Clear all data and start a new video"
                >
                  ↺ Start Fresh
                </button>
              )}
              <button onClick={onClose} className="h-9 w-9 rounded-full bg-[#1B2130] text-[#A8B3CF] hover:text-white">✕</button>
            </div>
          </div>

          {showStartFreshModal && createPortal(
            <div className="fixed inset-0 z-[10020] flex items-center justify-center p-4">
              <button
                type="button"
                className="absolute inset-0 bg-black/65 backdrop-blur-[2px]"
                onClick={() => setShowStartFreshModal(false)}
                aria-label="Close start fresh confirmation"
              />
              <div className="relative w-full max-w-md rounded-2xl border border-[#2A3550] bg-[#0B1220] shadow-[0_20px_60px_rgba(0,0,0,0.6)]">
                <div className="px-5 py-4 border-b border-[#1f2a44]">
                  <h3 className="text-white font-semibold text-base">Start Fresh?</h3>
                </div>
                <div className="px-5 py-4 text-sm text-[#AFC1E5] leading-relaxed">
                  This clears your script, plan, and storyboard. Your generation history is not affected.
                </div>
                <div className="px-5 pb-5 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowStartFreshModal(false)}
                    className="px-4 py-2 rounded-lg border border-[#334155] text-[#9FB0CF] hover:text-white hover:border-[#475569] text-sm font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowStartFreshModal(false);
                      onStartFresh();
                    }}
                    className="px-4 py-2 rounded-lg bg-[#3B82F6] hover:bg-[#2563EB] text-white text-sm font-semibold"
                  >
                    Start Fresh
                  </button>
                </div>
              </div>
            </div>,
            document.body
          )}

          <div className="mt-4 grid grid-cols-3 gap-2 max-w-3xl">
            {["Script Input", "Plan & Metadata", "Storyboard Preview"].map((step, idx) => {
              const stepNum = idx + 1;
              const isCurrent = activeStep === stepNum;
              // Step is reachable if data for it exists (step 1 always, step 2 needs plan, step 3 needs preview)
              const isReachable = stepNum === 1 || (stepNum === 2 && !!plan) || (stepNum === 3 && !!plan && !!preview);
              const isComplete  = (stepNum === 2 && !!plan) || (stepNum === 3 && !!plan && !!preview);
              return (
                <button
                  key={step}
                  type="button"
                  disabled={!isReachable || loading || planning}
                  onClick={() => isReachable && !loading && !planning && setActiveStep(stepNum)}
                  title={!isReachable ? `Complete step ${stepNum - 1} first` : isCurrent ? 'Current step' : `Go to ${step}`}
                  className={`rounded-lg border px-3 py-2 text-xs font-semibold transition-all text-left ${
                    isCurrent
                      ? 'bg-[#10213F] border-[#2D4F8F] text-[#C5D8FF] ring-1 ring-[#2D4F8F]/40'
                      : isReachable
                      ? 'bg-[#0D1A2A] border-[#1E3352] text-[#7A9BC4] hover:border-[#2D4F8F] hover:text-[#C5D8FF] cursor-pointer'
                      : 'bg-[#0E121B] border-[#222A3A] text-[#3D4F6A] cursor-not-allowed opacity-50'
                  }`}
                >
                  {isComplete && !isCurrent && <span className="mr-1 text-emerald-400">✓</span>}
                  {idx + 1}. {step}
                </button>
              );
            })}
          </div>
        </div>

        <div className={`flex-1 min-h-0 ${stepState === 3 ? 'overflow-hidden' : 'overflow-y-auto px-6 py-6'}`}>
          <div className={stepState === 3 ? 'flex h-full' : 'xl:grid xl:grid-cols-[minmax(0,1fr)_320px] gap-6 items-start'}>
          <div className={stepState === 3 ? 'flex-1 min-w-0 h-full overflow-hidden' : ''}>
          {loading ? (
            <div className="py-10 flex flex-col items-center justify-center text-center">
              <div style={{
                width: '44px', height: '44px',
                border: '3px solid #27272A', borderTopColor: '#3B82F6',
                borderRadius: '50%', animation: 'spin 0.8s linear infinite',
                marginBottom: '16px',
              }} />
              <div className="text-white font-semibold">Generating your video...</div>
              <div className="text-[#71717A] text-sm mt-1">Usually takes 20–90 seconds depending on clip fetch + render.</div>
              <div className="text-[#52525B] text-xs mt-3">Please keep this window open.</div>
            </div>
          ) : planning ? (
            <div className="py-10 flex flex-col items-center justify-center text-center">
              <div style={{
                width: '44px', height: '44px',
                border: '3px solid #27272A', borderTopColor: '#8B5CF6',
                borderRadius: '50%', animation: 'spin 0.8s linear infinite',
                marginBottom: '16px',
              }} />
              <div className="text-white font-semibold">Generating Claude video plan...</div>
              <div className="text-[#71717A] text-sm mt-1">Optimizing script, SEO metadata, and retention hooks.</div>
            </div>
          ) : activeStep === 3 && plan && preview ? (
            <div className="h-full">
              <TimelinePreview
                scenes={previewScenes}
                onScenesChange={setPreviewScenes}
                onApprove={onGenerateVideo}
                onCancel={() => setActiveStep(2)}
                onRefresh={onGeneratePreview}
                estimatedCost={preview.estimated_cost}
                error={error}
                dryRun={form.dryRun !== false}
                imageProvider={form.image_provider || 'huggingface'}
              />
            </div>
          ) : activeStep === 2 && plan ? (
            <>
              <div className="mb-4 p-3 rounded-xl bg-[#06070A] border border-[#27272A]">
                <div className="text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-1">Final Script Preview</div>
                <div className="text-[11px] text-[#8B97B3] mb-2">Generated preview from Hook / Body / CTA</div>
                <div className="w-full min-h-[220px] bg-[#05060A] border border-[#20222A] rounded-xl p-3 text-sm text-[#CFCFD4] whitespace-pre-wrap leading-relaxed">
                  {getScriptPreviewText(editableHook, editableBody, editableCta)}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <div className="p-3 rounded-xl bg-[#09090B] border border-[#27272A]">
                  <div className="text-[10px] text-[#71717A] uppercase font-bold">Hook</div>
                  <div className="text-[11px] text-[#8B97B3] mt-1 mb-2">Editable — tweak before generating storyboard</div>
                  <textarea
                    value={editableHook}
                    onChange={(e) => onScriptStateChange({ hook: e.target.value }, { markModified: true })}
                    rows={4}
                    className="w-full bg-[#05060A] border border-[#27272A] rounded-xl p-3 text-sm text-[#E4E4E7] focus:border-[#3B82F6] outline-none"
                  />
                </div>
                <div className="p-3 rounded-xl bg-[#09090B] border border-[#27272A]">
                  <div className="text-[10px] text-[#71717A] uppercase font-bold">Body</div>
                  <div className="text-[11px] text-[#8B97B3] mt-1 mb-2">Editable — tweak before generating storyboard</div>
                  <textarea
                    value={editableBody}
                    onChange={(e) => onScriptStateChange({ body: e.target.value }, { markModified: true })}
                    rows={6}
                    className="w-full bg-[#05060A] border border-[#27272A] rounded-xl p-3 text-sm text-[#E4E4E7] focus:border-[#3B82F6] outline-none"
                  />
                </div>
                <div className="p-3 rounded-xl bg-[#09090B] border border-[#27272A]">
                  <div className="text-[10px] text-[#71717A] uppercase font-bold">CTA</div>
                  <div className="text-[11px] text-[#8B97B3] mt-1 mb-2">Editable — tweak before generating storyboard</div>
                  <textarea
                    value={editableCta}
                    onChange={(e) => onScriptStateChange({ cta: e.target.value }, { markModified: true })}
                    rows={4}
                    className="w-full bg-[#05060A] border border-[#27272A] rounded-xl p-3 text-sm text-[#E4E4E7] focus:border-[#3B82F6] outline-none"
                  />
                </div>
              </div>

              {Array.isArray(plan.retention_notes) && plan.retention_notes.length > 0 && (
                <div className="mb-4 p-3 rounded-xl bg-purple-500/5 border border-purple-500/20">
                  <div className="text-[11px] font-bold text-purple-300 uppercase tracking-widest mb-2">Retention Notes (Claude)</div>
                  <ul className="list-disc pl-5 space-y-1 text-sm text-[#C4B5FD]">
                    {plan.retention_notes.map((note, idx) => <li key={idx}>{note}</li>)}
                  </ul>
                </div>
              )}

              <div className="mb-4">
                <div className="flex gap-2 mb-2">
                  {[
                    { key: 'youtube_shorts', label: 'YouTube Shorts' },
                    { key: 'reels', label: 'Reels' },
                    { key: 'tiktok', label: 'TikTok' },
                  ].map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setMetaTab(tab.key)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${metaTab === tab.key ? 'bg-[#3B82F6] text-white' : 'bg-[#09090B] text-[#A1A1AA] border border-[#27272A]'}`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
                <div className="p-3 rounded-xl bg-[#09090B] border border-[#27272A] space-y-2">
                  <div><span className="text-[10px] text-[#71717A] uppercase font-bold">Title</span><p className="text-sm text-[#E4E4E7] mt-1">{currentMeta.title}</p></div>
                  <div><span className="text-[10px] text-[#71717A] uppercase font-bold">Description</span><p className="text-sm text-[#E4E4E7] mt-1 whitespace-pre-wrap">{currentMeta.description}</p></div>
                  <div><span className="text-[10px] text-[#71717A] uppercase font-bold">Hashtags</span><p className="text-sm text-[#E4E4E7] mt-1">{currentMeta.hashtags}</p></div>
                  <button onClick={copyMeta} className="mt-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#27272A] text-[#A1A1AA] hover:text-white">Copy {metaTab} metadata</button>
                </div>
              </div>

              <div className="max-h-40 overflow-auto border border-[#27272A] rounded-xl mb-4">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left text-[#71717A] border-b border-[#27272A]"><th className="p-2">Scene</th><th className="p-2">Time</th><th className="p-2">Text</th></tr>
                  </thead>
                  <tbody>
                    {(plan.scenes || []).map((s, i) => (
                      <tr key={i} className="text-[#A1A1AA] border-b border-[#1f1f22]"><td className="p-2">{s.scene || i + 1}</td><td className="p-2">{s.start}s–{s.end}s</td><td className="p-2">{s.on_screen_text}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 mt-5 mb-4">
                <div>
                  <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Character Source</label>
                  <select
                    value={form.character_source || 'generate'}
                    onChange={(e) => setForm((prev) => ({ ...prev, character_source: e.target.value }))}
                    className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-3 text-white focus:border-[#3B82F6] outline-none"
                  >
                    <option value="generate">AI Generate (Gemini)</option>
                    <option value="preset">Preset Library</option>
                    <option value="upload">Upload Character Photo</option>
                  </select>
                </div>

                {form.character_source === 'preset' && (
                  <div>
                    <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Preset Character</label>
                    {(characterPresets || []).length === 0 ? (
                      <div className="p-3 rounded-xl bg-[#09090B] border border-[#27272A] text-xs text-[#52525B]">
                        No preset characters found. Use <span className="text-[#A1A1AA] font-semibold">AI Generate</span> to create a unique character, or <span className="text-[#A1A1AA] font-semibold">Upload</span> your own photo.
                      </div>
                    ) : (
                      <select
                        value={form.preset_id || ''}
                        onChange={(e) => setForm((prev) => ({ ...prev, preset_id: e.target.value }))}
                        className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-3 text-white focus:border-[#3B82F6] outline-none"
                      >
                        <option value="">Select preset</option>
                        {(characterPresets || []).slice(0, 100).map((preset) => (
                          <option key={preset.id} value={preset.id}>{preset.name}</option>
                        ))}
                      </select>
                    )}
                  </div>
                )}

                {form.character_source === 'upload' && (
                  <div className="md:col-span-2">
                    <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Upload Character Image</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        const reader = new FileReader();
                        reader.onload = () => {
                          const dataUrl = String(reader.result || '');
                          const base64 = dataUrl.includes(',') ? dataUrl.split(',')[1] : '';
                          setForm((prev) => ({ ...prev, uploaded_image_base64: base64 }));
                        };
                        reader.readAsDataURL(file);
                      }}
                      className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-3 text-white focus:border-[#3B82F6] outline-none"
                    />
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-3 mt-5">
                <button
                  onClick={() => setActiveStep(1)}
                  className="px-5 py-3 rounded-xl border border-[#3F3F46] text-[#A1A1AA] hover:text-white transition-all text-sm"
                >
                  ← Edit Script
                </button>
                {preview ? (
                  <>
                    <button
                      onClick={() => setActiveStep(3)}
                      className="flex-1 px-5 py-3 rounded-xl bg-[#0EA5E9] hover:bg-[#0284C7] text-white font-semibold transition-all"
                    >
                      Continue to Storyboard →
                    </button>
                    <button
                      onClick={onGeneratePreview}
                      disabled={loading}
                      className="px-5 py-3 rounded-xl border border-[#0EA5E9]/40 text-sky-300 hover:text-white hover:border-sky-400 transition-all text-sm disabled:opacity-40"
                    >
                      ↺ Re-generate Storyboard
                    </button>
                  </>
                ) : (
                  <button
                    onClick={onGeneratePreview}
                    disabled={loading}
                    className="flex-1 px-5 py-3 rounded-xl bg-[#0EA5E9] hover:bg-[#0284C7] text-white font-semibold transition-all disabled:opacity-40"
                  >
                    Generate Storyboard Preview
                  </button>
                )}
                <button
                  onClick={onRegeneratePlanFromEdits}
                  disabled={loading || planning || !editableScript.trim()}
                  className="px-5 py-3 rounded-xl border border-[#8B5CF6]/40 text-purple-300 hover:text-white hover:border-purple-400 transition-all text-sm disabled:opacity-40"
                >
                  ↻ Regenerate Plan from Edits
                </button>
                <button
                  onClick={async () => {
                    const confirmed = await confirmDialog({
                      title: 'Re-generate Claude Plan?',
                      message: 'This will clear the current plan and storyboard. Your script is preserved.',
                      confirmText: 'Re-generate Plan',
                      cancelText: 'Keep Current Plan',
                      tone: 'danger',
                    });
                    if (confirmed) {
                      onGeneratePlan(true);
                    }
                  }}
                  disabled={loading || planning}
                  className="px-5 py-3 rounded-xl border border-[#3F3F46] text-[#A1A1AA] hover:text-white transition-all text-sm disabled:opacity-40"
                >
                  ↺ Re-generate Plan
                </button>
              </div>
              {scriptModified && (
                <div className="mt-3 text-xs text-amber-300">
                  User-edited script is now the source of truth for preview and generation.
                </div>
              )}
            </>
          ) : (
            <>
          <div className="mb-3 flex items-center gap-2">
            <button
              onClick={() => setInputMode('script')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${inputMode === 'script' ? 'bg-[#3B82F6] text-white' : 'bg-[#09090B] text-[#A1A1AA] border border-[#27272A]'}`}
            >
              Script Mode
            </button>
            <button
              onClick={() => {
                setInputMode('clips');
                const parsed = parseClipsFromScript(form.script || '');
                if (parsed.length > 0) setClipRows(parsed);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${inputMode === 'clips' ? 'bg-[#3B82F6] text-white' : 'bg-[#09090B] text-[#A1A1AA] border border-[#27272A]'}`}
            >
              Clip Builder
            </button>
            <span className="text-[11px] text-[#71717A]">Use Clip Builder for correct format + URLs.</span>
          </div>

          {inputMode === 'script' ? (
            <>
              <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Full Script Preview</label>
              <div className="text-[11px] text-[#8B97B3] mb-2">Generated preview from Hook / Body / CTA</div>
              <div className="w-full min-h-[176px] bg-[#06070A] border border-[#27272A] rounded-xl p-4 text-[#CFCFD4] whitespace-pre-wrap leading-relaxed font-medium">
                {getScriptPreviewText(editableHook, editableBody, editableCta)}
              </div>
            </>
          ) : (
            <div className="space-y-3">
              {clipRows.map((clip, index) => (
                <div key={clip.id} className="p-3 rounded-xl bg-[#09090B] border border-[#27272A]">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-[11px] font-bold text-[#A1A1AA] uppercase tracking-widest">Clip {index + 1}</div>
                    <button
                      onClick={() => {
                        const next = clipRows.filter((row) => row.id !== clip.id);
                        const resolved = next.length > 0 ? next : [createEmptyClip(1)];
                        setClipRows(resolved);
                        onScriptStateChange({ full_script: buildScriptFromClips(resolved) }, { markModified: true, preserveFullScript: true });
                      }}
                      className="px-2 py-1 rounded-lg text-[11px] bg-[#27272A] text-[#A1A1AA] hover:text-white"
                    >
                      Remove
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
                    <div>
                      <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-1">Start</label>
                      <input
                        value={clip.start}
                        onChange={(e) => {
                          const next = clipRows.map((row) => row.id === clip.id ? { ...row, start: e.target.value } : row);
                          setClipRows(next);
                          onScriptStateChange({ full_script: buildScriptFromClips(next) }, { markModified: true, preserveFullScript: true });
                        }}
                        placeholder="0:00"
                        className="w-full bg-[#0f0f13] border border-[#27272A] rounded-lg p-2 text-white focus:border-[#3B82F6] outline-none text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-1">End</label>
                      <input
                        value={clip.end}
                        onChange={(e) => {
                          const next = clipRows.map((row) => row.id === clip.id ? { ...row, end: e.target.value } : row);
                          setClipRows(next);
                          onScriptStateChange({ full_script: buildScriptFromClips(next) }, { markModified: true, preserveFullScript: true });
                        }}
                        placeholder="0:05"
                        className="w-full bg-[#0f0f13] border border-[#27272A] rounded-lg p-2 text-white focus:border-[#3B82F6] outline-none text-sm"
                      />
                    </div>
                  </div>

                  <div className="mb-2">
                    <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-1">Text Overlay / Direction</label>
                    <textarea
                      value={clip.text}
                      onChange={(e) => {
                        const next = clipRows.map((row) => row.id === clip.id ? { ...row, text: e.target.value } : row);
                        setClipRows(next);
                        onScriptStateChange({ full_script: buildScriptFromClips(next) }, { markModified: true, preserveFullScript: true });
                      }}
                      placeholder='Wembley exterior B-roll + text overlay "2018 — ..."'
                      className="w-full bg-[#0f0f13] border border-[#27272A] rounded-lg p-2 text-white focus:border-[#3B82F6] outline-none h-20 resize-y text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-1">URL (Optional)</label>
                    <input
                      value={clip.url}
                      onChange={(e) => {
                        const next = clipRows.map((row) => row.id === clip.id ? { ...row, url: e.target.value } : row);
                        setClipRows(next);
                        onScriptStateChange({ full_script: buildScriptFromClips(next) }, { markModified: true, preserveFullScript: true });
                      }}
                      placeholder="https://www.pexels.com/video/... or direct .mp4 URL"
                      className="w-full bg-[#0f0f13] border border-[#27272A] rounded-lg p-2 text-white focus:border-[#3B82F6] outline-none text-sm"
                    />
                  </div>
                </div>
              ))}

              <div className="flex gap-2">
                <button
                  onClick={() => {
                    const next = [...clipRows, createEmptyClip(clipRows.length + 1)];
                    setClipRows(next);
                    onScriptStateChange({ full_script: buildScriptFromClips(next) }, { markModified: true, preserveFullScript: true });
                  }}
                  className="px-3 py-2 rounded-lg text-xs font-semibold bg-[#27272A] text-[#A1A1AA] hover:text-white"
                >
                  + Add Clip
                </button>
                <button
                  onClick={() => onScriptStateChange({ full_script: buildScriptFromClips(clipRows) }, { markModified: true, preserveFullScript: true })}
                  className="px-3 py-2 rounded-lg text-xs font-semibold bg-[#09090B] border border-[#27272A] text-[#A1A1AA] hover:text-white"
                >
                  Sync to Script
                </button>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
            <div>
              <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Hook (Optional)</label>
              <input
                value={editableHook}
                onChange={(e) => onScriptStateChange({ hook: e.target.value }, { markModified: true })}
                placeholder="Hook line"
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-3 text-white focus:border-[#3B82F6] outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Body (Optional)</label>
              <input
                value={editableBody}
                onChange={(e) => onScriptStateChange({ body: e.target.value }, { markModified: true })}
                placeholder="Body line"
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-3 text-white focus:border-[#3B82F6] outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">CTA (Optional)</label>
              <input
                value={editableCta}
                onChange={(e) => onScriptStateChange({ cta: e.target.value }, { markModified: true })}
                placeholder="CTA line"
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-3 text-white focus:border-[#3B82F6] outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 mt-4 max-w-[640px]">
            <div>
              <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Duration</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-2">
                {[
                  { value: 30, label: '30s Quick' },
                  { value: 45, label: '45s Standard' },
                  { value: 60, label: '60s Optimal' },
                  { value: 90, label: '90s Long' },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setForm(prev => ({ ...prev, duration_seconds: opt.value }))}
                    className={`px-3 py-2 rounded-lg text-xs font-semibold ${form.duration_seconds === opt.value ? 'bg-[#3B82F6] text-white' : 'bg-[#09090B] border border-[#27272A] text-[#A1A1AA] hover:text-white'}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              <input
                type="range"
                min="15"
                max="120"
                value={form.duration_seconds}
                onChange={(e) => setForm(prev => ({ ...prev, duration_seconds: Number(e.target.value) }))}
                className="w-full"
              />
              <div className="text-xs text-[#71717A] mt-1">
                {form.duration_seconds}s • {form.duration_seconds < 45 ? 'Too short for strong monetization' : form.duration_seconds <= 60 ? 'Optimal for YouTube Shorts' : 'Long-form Shorts storytelling'}
              </div>
            </div>
            <div>
              <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Video Style</label>
              <select
                value={form.scene_mode || 'auto'}
                onChange={e => setForm(prev => ({ ...prev, scene_mode: e.target.value }))}
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-3 text-white focus:border-[#3B82F6] outline-none"
              >
                {videoStyleOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              {/* Auto-label showing implied max scenes */}
              <p className="mt-1.5 text-[11px] text-[#52525B]">
                {form.scene_mode === 'ai' ? '⚡ All scenes use RunwayML (max credits)' : form.scene_mode === 'auto' ? '⚡ Up to 3 AI scenes + stock fill' : '✦ Stock footage only — no Runway spend'}
              </p>
            </div>
            <div>
              <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Niche</label>
              <input
                value={form.niche || 'general'}
                onChange={(e) => setForm(prev => ({ ...prev, niche: e.target.value }))}
                placeholder="productivity, AI tools, finance..."
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-3 text-white focus:border-[#3B82F6] outline-none"
              />
            </div>

            {/* Voice Selection */}
            <div>
              <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Voiceover</label>
              {/* Provider toggle */}
              <div className="grid grid-cols-2 gap-2 mb-3">
                <button
                  type="button"
                  onClick={() => setForm(prev => ({ ...prev, tts_provider: 'elevenlabs' }))}
                  className={`px-3 py-2.5 rounded-xl border text-xs font-semibold transition-all ${form.tts_provider !== 'free' ? 'bg-[#7C3AED]/15 border-[#7C3AED]/60 text-violet-300' : 'bg-[#09090B] border-[#27272A] text-[#A1A1AA] hover:text-white'}`}
                >
                  ⚡ ElevenLabs AI Voice
                  <span className="block text-[10px] font-normal opacity-70 mt-0.5">Uses your ElevenLabs credits</span>
                </button>
                <button
                  type="button"
                  onClick={() => setForm(prev => ({ ...prev, tts_provider: 'free' }))}
                  className={`px-3 py-2.5 rounded-xl border text-xs font-semibold transition-all ${form.tts_provider === 'free' ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300' : 'bg-[#09090B] border-[#27272A] text-[#A1A1AA] hover:text-white'}`}
                >
                  ✦ Free TTS (pyttsx3)
                  <span className="block text-[10px] font-normal opacity-70 mt-0.5">No credits — robotic voice</span>
                </button>
              </div>
              {/* Voice selector — shown only when ElevenLabs is selected */}
              {form.tts_provider !== 'free' && (
                <select
                  value={form.voice_id || '21m00Tcm4TlvDq8ikWAM'}
                  onChange={e => setForm(prev => ({ ...prev, voice_id: e.target.value }))}
                  className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-3 text-white focus:border-[#7C3AED] outline-none text-sm"
                >
                  <optgroup label="Female Voices">
                    <option value="21m00Tcm4TlvDq8ikWAM">Rachel — calm, narration (default)</option>
                    <option value="AZnzlk1XvdvUeBnXmlld">Domi — strong, confident</option>
                    <option value="EXAVITQu4vr4xnSDxMaL">Bella — soft, friendly</option>
                    <option value="MF3mGyEYCl7XYWbV9V6O">Elli — young, energetic</option>
                    <option value="jsCqWAovK2LkecY7zXl4">Dorothy — pleasant, clear</option>
                  </optgroup>
                  <optgroup label="Male Voices">
                    <option value="TxGEqnHWrfWFTfGW9XjX">Josh — deep, authoritative</option>
                    <option value="VR6AewLTigWG4xSOukaG">Arnold — strong, confident</option>
                    <option value="pNInz6obpgDQGcFmaJgB">Adam — neutral, professional</option>
                    <option value="yoZ06aMxZJJ28mfd3POQ">Sam — conversational, friendly</option>
                    <option value="ODq5zmih8GrVes37Dizd">Patrick — storytelling, warm</option>
                    <option value="GBv7mTt0atIp3Br8iCZE">Thomas — calm, measured</option>
                  </optgroup>
                </select>
              )}
              <p className="mt-1.5 text-[11px] text-[#52525B]">
                {form.tts_provider === 'free'
                  ? '✦ No ElevenLabs credits consumed — uses offline pyttsx3 engine'
                  : `⚡ ElevenLabs credits: ~${Math.ceil(((form.hook || '') + (form.body || '') + (form.cta || '')).length || 200)} chars per video`}
              </p>
            </div>

            {/* Image Source */}
            <div>
              <label className="block text-[11px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Storyboard Images</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setForm(prev => ({ ...prev, image_provider: 'pollinations' }))}
                  className={`px-3 py-2.5 rounded-xl border text-xs font-semibold transition-all ${form.image_provider === 'pollinations' ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300' : 'bg-[#09090B] border-[#27272A] text-[#A1A1AA] hover:text-white'}`}
                >
                  ◎ Pollinations
                  <span className="block text-[10px] font-normal opacity-70 mt-0.5">Free · Flux model</span>
                </button>
                <button
                  type="button"
                  onClick={() => setForm(prev => ({ ...prev, image_provider: 'huggingface' }))}
                  className={`px-3 py-2.5 rounded-xl border text-xs font-semibold transition-all ${form.image_provider === 'huggingface' ? 'bg-sky-500/15 border-sky-500/40 text-sky-300' : 'bg-[#09090B] border-[#27272A] text-[#A1A1AA] hover:text-white'}`}
                >
                  ⚡ HuggingFace
                  <span className="block text-[10px] font-normal opacity-70 mt-0.5">Free · FLUX.1-schnell</span>
                </button>
                <button
                  type="button"
                  onClick={() => setForm(prev => ({ ...prev, image_provider: 'gemini' }))}
                  className={`px-3 py-2.5 rounded-xl border text-xs font-semibold transition-all ${form.image_provider === 'gemini' ? 'bg-[#7C3AED]/15 border-[#7C3AED]/60 text-violet-300' : 'bg-[#09090B] border-[#27272A] text-[#A1A1AA] hover:text-white'}`}
                >
                  ✦ Gemini
                  <span className="block text-[10px] font-normal opacity-70 mt-0.5">Paid · Best quality</span>
                </button>
              </div>
              {form.image_provider === 'huggingface' && (
                <p className="mt-1.5 text-[11px] text-sky-400/80">⚡ Requires HF_TOKEN in .env — get one free at huggingface.co/settings/tokens. Falls back to Pollinations if token is missing.</p>
              )}
              {form.image_provider === 'gemini' && (
                <p className="mt-1.5 text-[11px] text-amber-400/80">⚠ Gemini image generation requires Google billing enabled. Falls back to Pollinations if quota exceeded.</p>
              )}
            </div>

            {/* Dry Run Toggle */}
            <div className={`rounded-xl border p-3 flex items-center justify-between gap-4 transition-colors ${form.dryRun ? 'border-emerald-500/40 bg-emerald-500/5' : 'border-amber-500/40 bg-amber-500/5'}`}>
              <div>
                <p className={`text-xs font-bold ${form.dryRun ? 'text-emerald-300' : 'text-amber-300'}`}>
                  {form.dryRun ? '🛡 Dry Run — No spend' : '🔴 Live Mode — Real credits'}
                </p>
                <p className="text-[11px] text-[#71717A] mt-0.5">
                  {form.dryRun ? 'Runway & ElevenLabs calls are skipped. Safe for UI testing.' : 'Real Runway & ElevenLabs API calls will be made and credits consumed.'}
                </p>
              </div>
              <button
                type="button"
                onClick={async () => {
                  if (form.dryRun) {
                    const confirmed = await confirmDialog({
                      title: 'Switch To Live Mode?',
                      message: 'Real RunwayML and ElevenLabs API calls will be made. Credits will be consumed.',
                      confirmText: 'Go Live',
                      cancelText: 'Stay In Dry Run',
                      tone: 'danger',
                    });
                    if (confirmed) {
                      setForm(prev => ({ ...prev, dryRun: false }));
                    }
                  } else {
                    setForm(prev => ({ ...prev, dryRun: true }));
                  }
                }}
                className={`relative flex-shrink-0 w-11 h-6 rounded-full transition-colors focus:outline-none ${form.dryRun ? 'bg-emerald-500' : 'bg-amber-500'}`}
              >
                <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${form.dryRun ? 'translate-x-0' : 'translate-x-5'}`} />
              </button>
            </div>
          </div>

          {(error || planError) && (
            <p className="text-red-400 text-sm font-semibold bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 mt-4">{error || planError}</p>
          )}

          <div className="flex gap-3 mt-5 sticky bottom-0 bg-[#0b0d12]/95 backdrop-blur py-3">
            <button
              onClick={onClose}
              className="px-5 py-3 rounded-xl border border-[#3F3F46] text-[#A1A1AA] hover:text-white transition-all"
              disabled={loading}
            >
              Cancel
            </button>
            {plan ? (
              <>
                <button
                  onClick={() => setActiveStep(2)}
                  className="flex-1 px-5 py-3 rounded-xl bg-[#8B5CF6] hover:bg-[#7C3AED] text-white font-semibold transition-all"
                >
                  Continue to Plan →
                </button>
                <button
                  disabled={loading || planning}
                  onClick={async () => {
                    const confirmed = await confirmDialog({
                      title: 'Re-generate Claude Plan?',
                      message: 'This will clear your existing plan and storyboard. Your script fields are preserved.',
                      confirmText: 'Re-generate Plan',
                      cancelText: 'Keep Current Plan',
                      tone: 'danger',
                    });
                    if (confirmed) {
                      onGeneratePlan(true);
                    }
                  }}
                  className="px-5 py-3 rounded-xl border border-[#6D28D9]/60 text-violet-300 hover:text-white hover:border-violet-400 transition-all text-sm disabled:opacity-40"
                >
                  ↺ Re-generate Plan
                </button>
              </>
            ) : (
              <button
                onClick={() => onGeneratePlan(true)}
                disabled={loading || planning}
                className="px-5 py-3 rounded-xl bg-[#8B5CF6] hover:bg-[#7C3AED] text-white font-semibold transition-all disabled:opacity-40"
              >
                Generate Claude Plan
              </button>
            )}
          </div>
            </>
          )}
          </div>

          <aside className={`hidden xl:block space-y-4 ${stepState === 3 ? 'flex-shrink-0 w-80 h-full overflow-y-auto p-4 border-l border-[#1f2430]' : 'sticky top-28'}`}>
            <div className="rounded-xl border border-[#27314A] bg-[#0D1320] p-4">
              <div className="text-[10px] uppercase tracking-widest text-[#7F8DB0] font-bold">Mode</div>
              <div className={`mt-2 inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${form.dryRun ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'}`}>
                {form.dryRun ? 'Dry Run' : 'Live'}
              </div>
              <p className="text-xs text-[#9AA6C6] mt-2 leading-relaxed">
                {form.dryRun
                  ? 'No Runway or ElevenLabs spend while testing UI and flow.'
                  : 'Live mode may consume generation and voice credits.'}
              </p>
            </div>

            <div className="rounded-xl border border-[#27314A] bg-[#0D1320] p-4">
              <div className="text-[10px] uppercase tracking-widest text-[#7F8DB0] font-bold">Run Summary</div>
              <div className="mt-3 space-y-2 text-sm">
                <div className="flex items-center justify-between text-[#A9B5D1]"><span>Estimated Credits</span><span className="text-white font-semibold">{displayedCredits}</span></div>
                <div className="flex items-center justify-between text-[#A9B5D1]"><span>Character Source</span><span className="text-white font-semibold">{form.character_source === 'generate' ? 'AI Generate' : form.character_source === 'preset' ? 'Preset Library' : form.character_source === 'upload' ? 'Upload Photo' : 'AI Generate'}</span></div>
                <div className="flex items-center justify-between text-[#A9B5D1]"><span>Scene Mode</span><span className="text-white font-semibold capitalize">{form.scene_mode || 'auto'}</span></div>
                <div className="flex items-center justify-between text-[#A9B5D1]"><span>Max AI Scenes</span><span className="text-white font-semibold">{form.scene_mode === 'ai' ? 'All' : form.scene_mode === 'auto' ? '3' : '0'}</span></div>
                <div className="flex items-center justify-between text-[#A9B5D1]"><span>Duration</span><span className="text-white font-semibold">{form.duration_seconds || 45}s</span></div>
                <div className="flex items-center justify-between text-[#A9B5D1]"><span>Voice</span><span className={`font-semibold text-xs ${form.tts_provider === 'free' ? 'text-emerald-300' : 'text-violet-300'}`}>{form.tts_provider === 'free' ? 'Free TTS' : 'ElevenLabs'}</span></div>
                <div className="flex items-center justify-between text-[#A9B5D1]"><span>Images</span><span className={`font-semibold text-xs ${form.image_provider === 'gemini' ? 'text-violet-300' : form.image_provider === 'huggingface' ? 'text-sky-300' : 'text-emerald-300'}`}>{form.image_provider === 'gemini' ? 'Gemini AI' : form.image_provider === 'huggingface' ? 'HuggingFace' : 'Pollinations'}</span></div>
              </div>
            </div>

            <div className="rounded-xl border border-[#27314A] bg-[#0D1320] p-4">
              <div className="text-[10px] uppercase tracking-widest text-[#7F8DB0] font-bold mb-3">Step Progress</div>
              <div className="space-y-2">
                {[
                  { label: 'Script Input',       done: true,    step: 1 },
                  { label: 'Claude Plan',         done: !!plan,  step: 2 },
                  { label: 'Storyboard Preview',  done: !!preview, step: 3 },
                ].map(({ label, done, step: s }) => (
                  <div
                    key={label}
                    onClick={() => {
                      const reachable = s === 1 || (s === 2 && !!plan) || (s === 3 && !!plan && !!preview);
                      if (reachable && !loading && !planning) setActiveStep(s);
                    }}
                    className={`flex items-center gap-2 text-xs rounded-lg px-2 py-1.5 transition-colors ${
                      activeStep === s
                        ? 'bg-[#10213F] text-[#C5D8FF]'
                        : done
                        ? 'text-[#7A9BC4] hover:bg-[#10213F]/50 cursor-pointer'
                        : 'text-[#3D4F6A] cursor-not-allowed'
                    }`}
                  >
                    <span className={done ? 'text-emerald-400' : 'text-[#3D4F6A]'}>{done ? '✓' : '○'}</span>
                    <span>{s}. {label}</span>
                    {activeStep === s && <span className="ml-auto text-[10px] text-[#2D4F8F] font-bold">HERE</span>}
                  </div>
                ))}
              </div>
              {/* CTA based on current step + data state */}
              <div className="mt-3 pt-3 border-t border-[#1E2D40]">
                {activeStep === 1 && !plan && (
                  <button
                    onClick={() => onGeneratePlan(true)}
                    disabled={loading || planning}
                    className="w-full px-3 py-2 rounded-lg bg-[#8B5CF6] hover:bg-[#7C3AED] text-white text-sm font-semibold disabled:opacity-40 transition-colors"
                  >
                    Generate Claude Plan
                  </button>
                )}
                {activeStep === 1 && plan && (
                  <button
                    onClick={() => setActiveStep(2)}
                    className="w-full px-3 py-2 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-sm font-semibold transition-colors"
                  >
                    Continue to Plan →
                  </button>
                )}
                {activeStep === 2 && !preview && (
                  <button
                    onClick={onGeneratePreview}
                    disabled={loading}
                    className="w-full px-3 py-2 rounded-lg bg-[#0EA5E9] hover:bg-[#0284C7] text-white text-sm font-semibold disabled:opacity-40 transition-colors"
                  >
                    Generate Storyboard Preview
                  </button>
                )}
                {activeStep === 2 && preview && (
                  <button
                    onClick={() => setActiveStep(3)}
                    className="w-full px-3 py-2 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-sm font-semibold transition-colors"
                  >
                    Continue to Storyboard →
                  </button>
                )}
                {activeStep === 3 && (
                  <button
                    onClick={onGenerateVideo}
                    disabled={loading}
                    className="w-full px-3 py-2 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-sm font-semibold disabled:opacity-40 transition-colors"
                  >
                    Approve &amp; Generate Video
                  </button>
                )}
              </div>
            </div>
          </aside>
          </div>
        </div>
      </div>
    </div>
  );
}

function OutputSection({ output, platform }) {
  const items = Array.isArray(output) ? output : (output ? [output] : []);
  if (!items.length) return null;
  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div key={i} className="bg-[#09090B] border border-[#27272A] rounded-xl p-4">
          <div className="flex items-start justify-between gap-4">
            <p className="text-[#E4E4E7] text-sm leading-relaxed flex-1 whitespace-pre-wrap">{typeof item === 'string' ? item : item.text || JSON.stringify(item)}</p>
            <CopyButton text={typeof item === 'string' ? item : item.text || JSON.stringify(item)} />
          </div>
        </div>
      ))}
    </div>
  );
}

function LoadingState() {
  const [currentStep, setCurrentStep] = useState(0);
  const [dots, setDots] = useState('');

  const steps = [
    { icon: '🔍', text: 'Reading your content...' },
    { icon: '🧠', text: 'Finding the best angle...' },
    { icon: '✍️', text: 'Writing your Twitter thread...' },
    { platform: 'linkedin', text: 'Crafting your LinkedIn post...' },
    { platform: 'tiktok', text: 'Scripting your TikTok...' },
    { platform: 'reels', text: 'Optimizing Instagram Reels...' },
    { platform: 'shorts', text: 'Creating YouTube Shorts metadata...' },
    { icon: '⚡', text: 'Almost ready...' },
  ];

  useEffect(() => {
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => prev < steps.length - 1 ? prev + 1 : prev);
    }, 2500);
    const dotsInterval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 400);
    return () => {
      clearInterval(stepInterval);
      clearInterval(dotsInterval);
    };
  }, []);

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '60px 24px', textAlign: 'center',
    }}>
      <div style={{
        width: '64px', height: '64px', borderRadius: '16px',
        background: 'linear-gradient(135deg, #3B82F6, #1D4ED8)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: '32px', animation: 'pulse 1.5s ease-in-out infinite',
      }}>
        <span style={{ fontSize: '28px' }}>⚡</span>
      </div>

      <div style={{ fontSize: '20px', fontWeight: 700, color: '#FAFAFA', marginBottom: '8px', minHeight: '32px' }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
          {steps[currentStep].platform ? (
            <SocialPlatformIcon platform={steps[currentStep].platform} className="w-5 h-5" />
          ) : (
            <span>{steps[currentStep].icon}</span>
          )}
          <span>{steps[currentStep].text}{dots}</span>
        </span>
      </div>
      <div style={{ color: '#52525B', fontSize: '14px', marginBottom: '40px' }}>
        Powered by Claude AI · Usually takes 10-20 seconds
      </div>

      <div style={{
        width: '100%', maxWidth: '320px', height: '4px', background: '#18181B',
        borderRadius: '2px', overflow: 'hidden', marginBottom: '32px',
      }}>
        <div style={{
          height: '100%', background: 'linear-gradient(90deg, #3B82F6, #60A5FA)',
          borderRadius: '2px', width: `${((currentStep + 1) / steps.length) * 100}%`,
          transition: 'width 0.5s ease',
        }} />
      </div>

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        {steps.map((step, index) => (
          <div key={index} style={{
            width: index === currentStep ? '24px' : '8px',
            height: '8px', borderRadius: '4px',
            background: index <= currentStep ? '#3B82F6' : '#27272A',
            transition: 'all 0.3s ease',
          }} />
        ))}
      </div>

      <div style={{
        marginTop: '40px', padding: '12px 20px', background: '#0D0D0F',
        border: '1px solid #1C1C1F', borderRadius: '8px', maxWidth: '360px',
      }}>
        <div style={{ color: '#52525B', fontSize: '11px', fontWeight: 700, letterSpacing: '1px', marginBottom: '4px' }}>
          DID YOU KNOW
        </div>
        <div style={{ color: '#71717A', fontSize: '13px', lineHeight: 1.5 }}>
          Twitter threads get 3x more impressions than single tweets on average.
        </div>
      </div>
    </div>
  );
}

export default function Dashboard({ mode = 'generate' }) {
  const { user, refreshUser } = useAuth();
  const { confirm: confirmDialog } = useDialog();
  const [inputType, setInputType] = useState('url');
  const [content, setContent] = useState('');
  const [tone, setTone] = useState('professional');
  const [platforms, setPlatforms] = useState(['twitter', 'linkedin', 'tiktok']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [genFailed, setGenFailed] = useState(false);
  const [limitReached, setLimitReached] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(null);
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [checkoutClientSecret, setCheckoutClientSecret] = useState(null);
  const [output, setOutput] = useState(null);
  const [usage, setUsage] = useState(null);
  const [activeTab, setActiveTab] = useState(null);
  const [videoMetadata, setVideoMetadata] = useState(null);
  const [currentGenerationId, setCurrentGenerationId] = useState(null);
  const [reelsMeta, setReelsMeta] = useState(null);
  const [shortsMeta, setShortsMeta] = useState(null);
  const [hookVariations, setHookVariations] = useState(null);
  const [hookVersions, setHookVersions] = useState({});
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoPlanning, setVideoPlanning] = useState(false);
  const [videoError, setVideoError] = useState('');
  const [videoPlanError, setVideoPlanError] = useState('');
  const [videoResult, setVideoResult] = useState(null);
  const [videoPlan, setVideoPlan] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [previewScenes, setPreviewScenes] = useState([]);
  const [videoScriptState, setVideoScriptState] = useState(() => createScriptState());
  const [videoScriptModified, setVideoScriptModified] = useState(false);
  const [characterPresets, setCharacterPresets] = useState([]);
  const [videoMode, setVideoMode] = useState({ dry_run: true, mode_label: 'Dry Run' });
  const [showVideoEditor, setShowVideoEditor] = useState(false);
  const [selectedVideoEditorItem, setSelectedVideoEditorItem] = useState(null);
  const [videoEditorBlobUrl, setVideoEditorBlobUrl] = useState('');
  const [videoMetaTab, setVideoMetaTab] = useState('youtube_shorts');
  const [videoBlobUrl, setVideoBlobUrl] = useState('');
  const [videoHistory, setVideoHistory] = useState([]);
  const [videoHistoryLoading, setVideoHistoryLoading] = useState(false);
  const [videoHistorySearch, setVideoHistorySearch] = useState('');
  const [videoHistoryStatus, setVideoHistoryStatus] = useState('all');
  const [videoAnalytics, setVideoAnalytics] = useState(null);
  const [videoAnalyticsLoading, setVideoAnalyticsLoading] = useState(false);
  const [analyticsHideZero, setAnalyticsHideZero] = useState(true);
  const [apiCredits, setApiCredits] = useState(null);
  const [apiCreditsLoading, setApiCreditsLoading] = useState(false);
  const [videoHistoryPage, setVideoHistoryPage] = useState(0);
  const [batchTopics, setBatchTopics] = useState('');
  const [batchResult, setBatchResult] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchStatusLoading, setBatchStatusLoading] = useState(false);
  const [activeGenerationId, setActiveGenerationId] = useState(null);
  const [activeGenerationProgress, setActiveGenerationProgress] = useState(null);
  const [deletingVideoId, setDeletingVideoId] = useState(null);
  const [videoForm, setVideoForm] = useState({
    script: '',
    hook: '',
    body: '',
    cta: '',
    duration_seconds: 45,
    scene_mode: 'stock',
    niche: 'general',
    character_source: 'generate',
    preset_id: '',
    uploaded_image_base64: '',
    dryRun: true,
    tts_provider: 'free',
    voice_id: '21m00Tcm4TlvDq8ikWAM',
    image_provider: 'huggingface',
  });
  const [workflowDismissed, setWorkflowDismissed] = useState(
    () => localStorage.getItem('tf_workflow_dismissed') === '1'
  );

  const usageCount = usage?.used ?? user?.usage_count ?? 0;
  const usageLimit = usage?.limit ?? user?.usage_limit ?? 5;
  const plan = usage?.plan ?? user?.plan ?? 'free';
  const atLimit = usageCount >= usageLimit;

  const handleTogglePlatform = (p) => {
    setPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]);
  };

  const handleGenerate = async () => {
    if (!content.trim()) return setError('Please enter some content or a URL');
    if (platforms.length === 0) return setError('Select at least one platform');
    setLoading(true);
    setError('');
    setGenFailed(false);
    setLimitReached(false);
    setOutput(null);
    setVideoMetadata(null);
    setHookVariations(null);
    setHookVersions({});
    try {
      const data = await api.generate({ input_type: inputType, content, platforms, tone });
      if (!data.success) {
        setGenFailed(true);
        setError(data.error || 'Generation failed. Please try again.');
        return;
      }
      setOutput(data.data);
      setUsage(data.usage);
      setVideoMetadata(data.video_metadata || null);
      setCurrentGenerationId(data.generation_id || null);
      setReelsMeta((data.reels_title || data.reels_description || data.reels_hashtags)
        ? { title: data.reels_title || '', description: data.reels_description || '', hashtags: data.reels_hashtags || '' }
        : null);
      setShortsMeta((data.shorts_title || data.shorts_description || data.shorts_tags)
        ? { title: data.shorts_title || '', description: data.shorts_description || '', tags: data.shorts_tags || '' }
        : null);
      setHookVariations(data.hook_variations || null);
      setHookVersions({});
      setActiveTab(platforms[0]);
      refreshUser();

      // Show toast when voice learning activates for the first time
      if (data.voice_just_learned) {
        const voiceToast = document.createElement('div');
        voiceToast.style.cssText = [
          'position:fixed', 'top:24px', 'right:24px',
          'background:linear-gradient(135deg,#8b5cf6,#7c3aed)',
          'color:white', 'padding:20px 28px', 'border-radius:12px',
          'box-shadow:0 8px 24px rgba(139,92,246,0.4)',
          'z-index:9999', 'display:flex', 'align-items:center',
          'gap:16px', 'min-width:300px',
        ].join(';');
        voiceToast.innerHTML = `
          <span style="font-size:32px">🎤</span>
          <div>
            <div style="font-size:16px;font-weight:700;margin-bottom:4px">Voice Learned!</div>
            <div style="font-size:13px;opacity:0.9">Future content will sound like you</div>
          </div>`;
        document.body.appendChild(voiceToast);
        setTimeout(() => {
          voiceToast.style.transition = 'opacity 0.3s';
          voiceToast.style.opacity = '0';
          setTimeout(() => voiceToast.remove(), 300);
        }, 5000);
      }
    } catch (err) {
      if (err.status === 429) {
        setLimitReached(true);
      } else {
        setGenFailed(true);
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan) => {
    setCheckoutLoading(plan);
    try {
      const data = await api.createCheckout(plan);
      if (data.clientSecret) {
        setCheckoutClientSecret(data.clientSecret);
        setShowCheckoutModal(true);
      } else {
        throw new Error('Could not create checkout session');
      }
    } catch (err) {
      setError('Could not open checkout. Please try again.');
    } finally {
      setCheckoutLoading(null);
    }
  };

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const checkoutPlan = urlParams.get('checkoutPlan');
    if (!checkoutPlan || (checkoutPlan !== 'solo' && checkoutPlan !== 'founder')) return;

    window.history.replaceState({}, '', '/dashboard');
    handleUpgrade(checkoutPlan);
  }, []);

  const openVideoModal = () => {
    setVideoError('');
    setVideoPlanError('');
    // Preserve in-progress session data (plan, storyboard, form) so users can
    // close and reopen the modal without losing their work.
    // Only initialise form with page content when there is genuinely no session data.
    if (!videoPlan && !videoPreview && !videoForm.script && !videoForm.hook) {
      const initialScript = inputType === 'text' ? content : '';
      setVideoForm((prev) => ({
        ...prev,
        script: initialScript,
      }));
      setVideoScriptState(createScriptState('', '', '', initialScript));
      setVideoScriptModified(false);
    }
    api.getVideoMode()
      .then((data) => setVideoMode(data || { dry_run: true, mode_label: 'Dry Run' }))
      .catch(() => setVideoMode({ dry_run: true, mode_label: 'Dry Run' }));
    api.getCharacterPresets()
      .then((data) => setCharacterPresets(Array.isArray(data?.presets) ? data.presets : []))
      .catch(() => setCharacterPresets([]));
    setShowVideoModal(true);
  };

  const resetVideoModal = () => {
    setVideoError('');
    setVideoPlanError('');
    setVideoPlan(null);
    setVideoPreview(null);
    setPreviewScenes([]);
    setVideoScriptState(createScriptState('', '', '', inputType === 'text' ? content : ''));
    setVideoScriptModified(false);
    setVideoForm({
      script: inputType === 'text' ? content : '',
      hook: '',
      body: '',
      cta: '',
      duration_seconds: 45,
      scene_mode: 'stock',
      niche: 'general',
      character_source: 'generate',
      preset_id: '',
      uploaded_image_base64: '',
      dryRun: true,
      tts_provider: 'free',
      voice_id: '21m00Tcm4TlvDq8ikWAM',
      image_provider: 'huggingface',
    });
  };

  const openVideoModalWithScript = (scriptText) => {
    resetVideoModal();
    openVideoModal();
    const nextScriptState = createScriptState('', '', '', scriptText || '');
    setVideoScriptState(nextScriptState);
    setVideoScriptModified(false);
    setVideoForm((prev) => ({ ...prev, script: nextScriptState.full_script, hook: '', body: '', cta: '' }));
  };

  const syncVideoScriptState = (partial, options = {}) => {
    const { markModified = false, preserveFullScript = false } = options;
    setVideoScriptState((prev) => {
      const nextHook = Object.prototype.hasOwnProperty.call(partial, 'hook') ? String(partial.hook || '') : prev.hook;
      const nextBody = Object.prototype.hasOwnProperty.call(partial, 'body') ? String(partial.body || '') : prev.body;
      const nextCta = Object.prototype.hasOwnProperty.call(partial, 'cta') ? String(partial.cta || '') : prev.cta;
      const nextFullScript = preserveFullScript
        ? String(partial.full_script ?? prev.full_script ?? '').trim()
        : composeScriptFromParts(nextHook, nextBody, nextCta);
      const nextState = createScriptState(nextHook, nextBody, nextCta, nextFullScript);
      setVideoForm((formPrev) => ({
        ...formPrev,
        script: nextState.full_script,
        hook: nextState.hook,
        body: nextState.body,
        cta: nextState.cta,
      }));
      if (markModified) setVideoScriptModified(true);
      return nextState;
    });
  };

  const openVideoStudioFromHistory = async (item) => {
    let hydratedItem = item;
    const needsHistoryDetail =
      hydratedItem?.id &&
      !hydratedItem?.plan &&
      !hydratedItem?.scenes &&
      !hydratedItem?.parts;

    if (needsHistoryDetail) {
      try {
        hydratedItem = await api.getVideoHistoryItem(hydratedItem.id);
      } catch (err) {
        setVideoError(err.message || 'Failed to load saved video details.');
        showDashboardToast(err.message || 'Failed to load saved video details.', 'error');
        return;
      }
    }

    const plan = hydratedItem?.plan || {};

    // Dry-run preview rows may store scenes under plan.scenes instead of item.scenes.
    const sceneSource =
      (Array.isArray(hydratedItem?.scenes) && hydratedItem.scenes.length > 0 && hydratedItem.scenes) ||
      (Array.isArray(plan?.scenes) && plan.scenes.length > 0 && plan.scenes) ||
      [];

    const sceneText = sceneSource
      .map((s) => s?.subtitle || s?.on_screen_text || s?.description || s?.visual_description || '')
      .filter(Boolean)
      .join(' ')
      .trim();

    const hook = (plan.hook || hydratedItem?.parts?.hook || '').trim();
    const body = (plan.body || hydratedItem?.parts?.body || '').trim();
    const cta = (plan.cta || hydratedItem?.parts?.cta || '').trim();
    const finalScript = (
      plan.final_script || [hook, body, cta].filter(Boolean).join(' ').trim() || sceneText
    ).trim();
    const niche = (plan.niche || hydratedItem?.niche || 'general').trim();
    const durationSeconds = hydratedItem?.duration_seconds || 45;

    // Full reset first so stale storyboard images from another video don't linger.
    resetVideoModal();
    openVideoModal();

    setVideoForm((prev) => ({
      ...prev,
      script: finalScript,
      hook,
      body,
      cta,
      duration_seconds: durationSeconds,
      niche,
    }));
    setVideoScriptState(createScriptState(hook, body, cta, finalScript));
    setVideoScriptModified(false);

    const safePlatformMeta = plan.platform_meta || item?.platform_meta || {
      youtube_shorts: {
        title: hydratedItem?.seo?.title || '',
        description: hydratedItem?.seo?.description || '',
        hashtags: Array.isArray(hydratedItem?.seo?.hashtags) ? hydratedItem.seo.hashtags.join(' ') : '',
      },
      reels: { title: '', description: '', hashtags: '' },
      tiktok: { title: '', description: '', hashtags: '' },
    };

    setVideoPlan({
      ...plan,
      final_script: finalScript,
      hook,
      body,
      cta,
      retention_notes: plan.retention_notes?.length
        ? plan.retention_notes
        : ['Reused from a previous generation — content restored from history.'],
      scenes: Array.isArray(plan.scenes) && plan.scenes.length > 0 ? plan.scenes : sceneSource,
      platform_meta: safePlatformMeta,
    });

    const hasPreviewImages = sceneSource.some((s) => !!s?.image_url);
    if (sceneSource.length > 0 && hasPreviewImages) {
      const restoredScenes = sceneSource.map((s, i) => ({
        id: s.id || `restored-${i}`,
        ...s,
        scene_index: s.scene_index ?? i,
        description: s.description || s.visual_description || s.on_screen_text || s.subtitle || '',
      }));

      setVideoPreview({
        preview_id: hydratedItem.run_id || `history-${hydratedItem.id}`,
        scenes: restoredScenes,
        estimated_cost: {
          credits: restoredScenes.reduce((acc, s) => acc + (Number(s.credits_cost) || 0), 0),
          usd: 0,
        },
      });
      setPreviewScenes(restoredScenes);
    } else {
      // Keep storyboard empty when historical scenes do not include image URLs
      // (e.g., rows generated directly via /video/free). User can regenerate preview.
      setVideoPreview(null);
      setPreviewScenes([]);
    }

    if (!finalScript && sceneSource.length === 0) {
      setVideoError('This history item has no reusable script/scene data.');
    }
  };

  const loadVideoHistory = async () => {
    setVideoHistoryLoading(true);
    try {
      const rows = await api.getVideoHistory();
      setVideoHistory(Array.isArray(rows) ? rows : []);
    } catch {
      setVideoHistory([]);
    } finally {
      setVideoHistoryLoading(false);
    }
  };

  const loadVideoAnalytics = async () => {
    setVideoAnalyticsLoading(true);
    try {
      const data = await api.getVideoAnalytics();
      setVideoAnalytics(data || null);
    } catch {
      setVideoAnalytics(null);
    } finally {
      setVideoAnalyticsLoading(false);
    }
  };

  const loadApiCredits = async () => {
    setApiCreditsLoading(true);
    try {
      const data = await api.getApiCredits();
      setApiCredits(data || null);
    } catch {
      setApiCredits(null);
    } finally {
      setApiCreditsLoading(false);
    }
  };

  const handleBatchGenerate = async () => {
    const topics = batchTopics
      .split('\n')
      .map((t) => t.trim())
      .filter(Boolean);
    if (topics.length === 0) {
      setVideoError('Please add at least one topic for batch generation.');
      return;
    }
    setBatchLoading(true);
    setVideoError('');
    try {
      const data = await api.generateVideoBatch({
        topics,
        duration: videoForm.duration_seconds || 45,
        style: videoForm.scene_mode || 'auto',
        niche: videoForm.niche || 'general',
      });
      setBatchResult(data);
    } catch (err) {
      setVideoError(err.message || 'Failed to queue batch videos.');
    } finally {
      setBatchLoading(false);
    }
  };

  const refreshBatchStatus = async () => {
    if (!batchResult?.batch_id) return;
    setBatchStatusLoading(true);
    try {
      const status = await api.getVideoBatchStatus(batchResult.batch_id);
      setBatchResult(status);
      loadVideoHistory();
      loadVideoAnalytics();
      loadApiCredits();
    } catch {
      // no-op
    } finally {
      setBatchStatusLoading(false);
    }
  };

  const handleGenerateVideoPlan = async (fromScratch = true, options = {}) => {
    const { preserveUserScript = videoScriptModified } = options;
    const authoritativeScript = createScriptState(
      videoScriptState.hook,
      videoScriptState.body,
      videoScriptState.cta,
      videoScriptState.full_script
    );
    if (!authoritativeScript.full_script.trim() && !(authoritativeScript.hook && authoritativeScript.body && authoritativeScript.cta)) {
      setVideoPlanError('Please paste a script or fill Hook, Body, and CTA fields.');
      return;
    }

    setVideoPlanning(true);
    setVideoPlanError('');
    // Only wipe existing plan+storyboard when the user explicitly asked for a fresh generate.
    // On a retry (fromScratch=false) we leave all existing data untouched.
    if (fromScratch) {
      setVideoPlan(null);
      setVideoPreview(null);
      setPreviewScenes([]);
    }
    try {
      const plan = await api.generateVideoPlan({
        ...videoForm,
        script: authoritativeScript.full_script,
        full_script: authoritativeScript.full_script,
        hook: authoritativeScript.hook,
        body: authoritativeScript.body,
        cta: authoritativeScript.cta,
      });
      const effectiveScriptState = preserveUserScript
        ? authoritativeScript
        : createScriptState(plan?.hook || '', plan?.body || '', plan?.cta || '', plan?.final_script || '');
      setVideoPlan({
        ...plan,
        final_script: effectiveScriptState.full_script,
        hook: effectiveScriptState.hook,
        body: effectiveScriptState.body,
        cta: effectiveScriptState.cta,
      });
      setVideoScriptState(effectiveScriptState);
      setVideoScriptModified(preserveUserScript ? true : false);
      setVideoForm((prev) => ({
        ...prev,
        script: effectiveScriptState.full_script,
        hook: effectiveScriptState.hook,
        body: effectiveScriptState.body,
        cta: effectiveScriptState.cta,
      }));
    } catch (err) {
      setVideoPlanError(err.message || 'Failed to generate Claude plan.');
    } finally {
      setVideoPlanning(false);
    }
  };

  const handleGenerateVideoPreview = async () => {
    const scriptState = createScriptState(
      videoScriptState.hook,
      videoScriptState.body,
      videoScriptState.cta,
      videoScriptState.full_script
    );
    const script = scriptState.full_script.trim();
    if (!script.trim()) {
      setVideoError('Please provide a script before generating preview.');
      return;
    }

    setVideoLoading(true);
    setVideoError('');
    setVideoPreview(null);
    setPreviewScenes([]);
    try {
      const preview = await api.generateVideoPreview({
        script,
        full_script: script,
        hook: scriptState.hook,
        body: scriptState.body,
        cta: scriptState.cta,
        duration: videoForm.duration_seconds || 45,
        niche: videoForm.niche || 'general',
        character_source: videoForm.character_source || 'generate',
        preset_id: videoForm.preset_id || null,
        uploaded_image_base64: videoForm.uploaded_image_base64 || null,
        scene_mode: videoForm.scene_mode || 'auto',
        image_provider: videoForm.image_provider || 'pollinations',
      });
      setVideoPreview(preview);
      setPreviewScenes(Array.isArray(preview?.scenes) ? preview.scenes : []);
    } catch (err) {
      setVideoError(err.message || 'Failed to generate storyboard preview.');
    } finally {
      setVideoLoading(false);
    }
  };

  const handleGenerateVideo = async () => {
    if (!videoPlan) {
      setVideoError('Please generate and confirm a Claude plan first.');
      return;
    }

    setVideoLoading(true);
    setVideoError('');
    try {
      const scriptState = createScriptState(
        videoScriptState.hook,
        videoScriptState.body,
        videoScriptState.cta,
        videoScriptState.full_script
      );
      if (videoPreview?.preview_id && previewScenes.length > 0) {
        // Background task — queued successfully. Keep modal open so plan/preview
        // are preserved and the user can retry if the background task fails.
        const queue = await api.generateVideoFromPreview({
          preview_id: videoPreview.preview_id,
          approved_scenes: previewScenes,
          dry_run: videoForm.dryRun !== false,  // safety: default true if undefined
          script: scriptState.full_script,
          full_script: scriptState.full_script,
          hook: scriptState.hook,
          body: scriptState.body,
          cta: scriptState.cta,
          niche: videoForm.niche || 'general',
          tts_provider: videoForm.tts_provider || 'free',
          voice_id: videoForm.voice_id || '21m00Tcm4TlvDq8ikWAM',
          confirmed_plan: videoPlan ? {
            ...videoPlan,
            final_script: scriptState.full_script,
            hook: scriptState.hook,
            body: scriptState.body,
            cta: scriptState.cta,
            user_modified: videoScriptModified,
          } : null,
        });

        setVideoResult({
          success: true,
          status: queue.status,
          message: queue.message || 'Video generation started in background.',
          dry_run: queue.dry_run,
          duration_seconds: videoForm.duration_seconds,
          queued: true,
        });

        // Start progress polling if backend returned a generation_id
        if (queue.generation_id) {
          setActiveGenerationId(queue.generation_id);
          setActiveGenerationProgress({ percent: 2, message: 'Queued...', step: 'queued' });
        }

        setShowVideoModal(false);
        loadVideoHistory();
        return;
      }

      const sceneMode = videoForm.scene_mode || 'auto';
      const derivedMaxScenes = sceneMode === 'ai' ? 99 : sceneMode === 'auto' ? 3 : 0;
      const payload = {
        script: scriptState.full_script,
        full_script: scriptState.full_script,
        hook: scriptState.hook,
        body: scriptState.body,
        cta: scriptState.cta,
        duration_seconds: videoForm.duration_seconds,
        confirmed_plan: {
          ...videoPlan,
          final_script: scriptState.full_script,
          hook: scriptState.hook,
          body: scriptState.body,
          cta: scriptState.cta,
          user_modified: videoScriptModified,
        },
        scene_mode: sceneMode,
        niche: videoForm.niche || 'general',
        dry_run: videoForm.dryRun === true,
        max_scenes: derivedMaxScenes,
        tts_provider: videoForm.tts_provider || 'free',
        voice_id: videoForm.voice_id || '21m00Tcm4TlvDq8ikWAM',
        image_provider: videoForm.image_provider || 'huggingface',
      };
      const res = await api.generateFreeVideo(payload);
      setVideoResult(res);

      if (videoBlobUrl) {
        URL.revokeObjectURL(videoBlobUrl);
      }
      const blobResult = await api.fetchVideoBlob(res.preview_url || res.download_url);
      setVideoBlobUrl(blobResult.blobUrl);
      setShowVideoModal(false);
      loadVideoHistory();
    } catch (err) {
      // DO NOT close the modal or clear any state on error.
      // All plan, preview, and scene data remain intact so the user can retry
      // without spending Claude tokens again.
      setVideoError(err.message || 'Video generation failed. Your plan and storyboard are preserved — click Approve & Generate to retry.');
    } finally {
      setVideoLoading(false);
    }
  };

  const handleRegeneratePlanFromEdits = async () => {
    await handleGenerateVideoPlan(true, { preserveUserScript: true });
  };

  const downloadHistoryVideo = async (downloadUrl, fallbackName) => {
    try {
      const { blobUrl } = await api.fetchVideoBlob(downloadUrl);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = fallbackName || 'video.mp4';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
    } catch {
      // no-op
    }
  };

  const showDashboardToast = (message, type = 'success') => {
    const toast = document.createElement('div');
    const palette = type === 'error'
      ? 'background:linear-gradient(135deg,#ef4444,#dc2626);box-shadow:0 10px 26px rgba(220,38,38,0.35);'
      : 'background:linear-gradient(135deg,#10b981,#059669);box-shadow:0 10px 26px rgba(5,150,105,0.35);';
    toast.style.cssText = [
      'position:fixed',
      'bottom:24px',
      'right:24px',
      'color:#fff',
      'padding:12px 18px',
      'border-radius:10px',
      'font-size:13px',
      'font-weight:700',
      'letter-spacing:0.01em',
      'z-index:9999',
      palette,
    ].join(';');
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = 'opacity 0.25s ease';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 260);
    }, 2400);
  };

  const handleDeleteVideoHistoryItem = async (item) => {
    const title = item?.seo?.title || item?.run_id || `Video ${item?.id}`;
    const confirmed = await confirmDialog({
      title: 'Delete Video Permanently?',
      message:
        `This will permanently delete ${title} and all related generated files (video, thumbnail, and scene assets).\n\n` +
        'This action cannot be undone.',
      confirmText: 'Delete Permanently',
      cancelText: 'Keep Video',
      tone: 'danger',
    });
    if (!confirmed) return;

    try {
      setDeletingVideoId(item.id);
      await api.deleteVideoHistoryItem(item.id);
      setVideoHistory((prev) => prev.filter((row) => row.id !== item.id));

      if (activeGenerationId === item.id) {
        setActiveGenerationId(null);
        setActiveGenerationProgress(null);
      }
      if (selectedVideoEditorItem?.id === item.id) {
        setShowVideoEditor(false);
        setSelectedVideoEditorItem(null);
      }

      loadVideoAnalytics();
      loadApiCredits();
      showDashboardToast('Video deleted permanently.');
    } catch (err) {
      if (err?.status === 404) {
        try {
          const refreshed = await api.getVideoHistory();
          setVideoHistory(Array.isArray(refreshed) ? refreshed : []);
          const stillExists = Array.isArray(refreshed) && refreshed.some((row) => Number(row.id) === Number(item.id));

          if (!stillExists) {
            showDashboardToast('Video was already removed.');
          } else {
            setVideoError('Delete API route was not found. Restart backend to load the latest delete endpoint.');
            showDashboardToast('Delete API not loaded. Restart backend.', 'error');
          }
        } catch {
          setVideoError('Delete failed and history refresh failed. Please retry.');
          showDashboardToast('Delete failed. Please retry.', 'error');
        }
      } else {
        setVideoError(err.message || 'Failed to delete video.');
        showDashboardToast(err.message || 'Failed to delete video.', 'error');
      }
    } finally {
      setDeletingVideoId(null);
    }
  };

  const handleSaveVideoEditor = async (payload) => {
    try {
      await api.saveVideoEditorChanges(payload);
      setShowVideoEditor(false);
      setSelectedVideoEditorItem(null);
      loadVideoHistory();
    } catch (err) {
      setVideoError(err.message || 'Failed to save video editor changes.');
    }
  };

  const openVideoEditor = async (item, options = {}) => {
    try {
      if (!item?.video_url) {
        // Dry-run / preview-only history items have no rendered video file yet.
        // Fall back to Studio reuse so user can edit script/plan/scenes immediately.
        await openVideoStudioFromHistory(item);
        return;
      }

      let hydratedItem = item;
      const needsHistoryDetail =
        hydratedItem?.id &&
        (!hydratedItem?.platform_meta || !hydratedItem?.editor);

      if (needsHistoryDetail) {
        try {
          hydratedItem = await api.getVideoHistoryItem(hydratedItem.id);
        } catch (err) {
          setVideoError(err.message || 'Failed to load video details.');
          return;
        }
      }

      let blobUrl = options.blobUrl || '';
      if (!blobUrl && hydratedItem?.video_url) {
        const result = await api.fetchVideoBlob(hydratedItem.video_url);
        blobUrl = result.blobUrl;
      }

      if (videoEditorBlobUrl) {
        URL.revokeObjectURL(videoEditorBlobUrl);
      }

      setVideoEditorBlobUrl(blobUrl || '');
      setSelectedVideoEditorItem(hydratedItem);
      setShowVideoEditor(true);
    } catch (err) {
      setVideoError(err.message || 'Unable to open video in browser.');
    }
  };

  const handleCloseCheckout = () => {
    setShowCheckoutModal(false);
    setCheckoutClientSecret(null);
  };

  const showHookToast = () => {
    const toast = document.createElement('div');
    toast.textContent = '🔥 Hook updated!';
    toast.style.cssText = 'position:fixed;bottom:24px;right:24px;background:linear-gradient(135deg,#10b981,#059669);color:white;padding:12px 24px;border-radius:8px;font-size:14px;font-weight:600;z-index:9999;box-shadow:0 4px 12px rgba(16,185,129,0.3);';
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = 'opacity 0.3s';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  };

  const handleHookSelect = (platform, hook) => {
    if (platform === 'reels') {
      setReelsMeta(prev => prev ? { ...prev, title: hook } : prev);
      setHookVersions(prev => ({ ...prev, reels: (prev.reels || 0) + 1 }));
      api.saveEdit(currentGenerationId, 'reels_title', hook).catch(() => {});
    } else if (platform === 'shorts') {
      setShortsMeta(prev => prev ? { ...prev, title: hook } : prev);
      setHookVersions(prev => ({ ...prev, shorts: (prev.shorts || 0) + 1 }));
      api.saveEdit(currentGenerationId, 'shorts_title', hook).catch(() => {});
    } else {
      const newContent = replaceHookInContent(output[platform] || '', hook, platform);
      setOutput(prev => ({ ...prev, [platform]: newContent }));
      setHookVersions(prev => ({ ...prev, [platform]: (prev[platform] || 0) + 1 }));
      api.saveEdit(currentGenerationId, platform, newContent).catch(() => {});
    }
    showHookToast();
  };

  // Detect Stripe redirect with session_id and activate plan via direct API call
  useEffect(() => {
    const handlePaymentSuccess = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const sessionId = urlParams.get('session_id');
      if (!sessionId) return;

      console.log('💳 Payment complete — Session ID:', sessionId);
      window.history.replaceState({}, '', '/dashboard');

      // Show loading toast immediately
      const loadingToast = document.createElement('div');
      loadingToast.id = 'payment-loading';
      loadingToast.style.cssText = 'position:fixed;top:20px;right:20px;background:linear-gradient(135deg,#3b82f6,#2563eb);color:white;padding:16px 24px;border-radius:12px;box-shadow:0 8px 24px rgba(59,130,246,0.4);z-index:9999;font-weight:600;display:flex;align-items:center;gap:12px;';
      loadingToast.innerHTML = '<span>⏳ Activating your subscription...</span>';
      document.body.appendChild(loadingToast);

      let activatedPlan = null;
      try {
        // Directly verify + update via backend (no Stripe CLI needed)
        const result = await api.verifySession(sessionId);
        console.log('🔍 Verify session result:', result);
        if (result.status === 'ok' && result.plan !== 'free') {
          activatedPlan = result.plan;
        }
      } catch (err) {
        console.error('❌ verifySession error:', err);
      }

      // Refresh user state from DB
      const updatedUser = await refreshUser();
      if (!activatedPlan && updatedUser?.plan !== 'free') {
        activatedPlan = updatedUser.plan;
      }

      const existing = document.getElementById('payment-loading');
      if (existing) existing.remove();

      if (activatedPlan) {
        const planLabel = activatedPlan === 'solo' ? '⚡ Solo' : '⭐ Founder';
        const successToast = document.createElement('div');
        successToast.style.cssText = 'position:fixed;top:20px;right:20px;background:linear-gradient(135deg,#10b981,#059669);color:white;padding:16px 24px;border-radius:12px;box-shadow:0 8px 24px rgba(16,185,129,0.4);z-index:9999;font-weight:600;display:flex;align-items:center;gap:12px;';
        successToast.innerHTML = `<span style="font-size:24px">🎉</span><div><div>${planLabel} plan activated!</div><div style="font-size:13px;opacity:.9;margin-top:4px">Ready to generate content</div></div>`;
        document.body.appendChild(successToast);
        setLimitReached(false);
        setUsage(null);
        try {
          const ctx = new (window.AudioContext || window.webkitAudioContext)();
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.connect(gain); gain.connect(ctx.destination);
          osc.frequency.value = 800;
          gain.gain.setValueAtTime(0.3, ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
          osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.5);
        } catch (_) {}
        setTimeout(() => {
          successToast.style.transition = 'opacity 0.3s';
          successToast.style.opacity = '0';
          setTimeout(() => successToast.remove(), 300);
        }, 5000);
      } else {
        const warnToast = document.createElement('div');
        warnToast.style.cssText = 'position:fixed;top:20px;right:20px;background:linear-gradient(135deg,#f59e0b,#d97706);color:white;padding:16px 24px;border-radius:12px;box-shadow:0 8px 24px rgba(245,158,11,0.4);z-index:9999;font-weight:600;display:flex;align-items:center;gap:12px;';
        warnToast.innerHTML = '<span style="font-size:24px">⚠️</span><div><div>Payment received — still processing</div><div style="font-size:13px;opacity:.9;margin-top:4px">Please refresh in a moment</div><button onclick="window.location.reload()" style="margin-top:8px;background:rgba(255,255,255,0.25);border:1px solid rgba(255,255,255,0.4);color:white;padding:4px 12px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;">Refresh →</button></div>';
        document.body.appendChild(warnToast);
        setTimeout(() => warnToast.remove(), 15000);
      }
    };
    handlePaymentSuccess();
  }, []);

  useEffect(() => {
    return () => {
      if (videoBlobUrl) URL.revokeObjectURL(videoBlobUrl);
      if (videoEditorBlobUrl) URL.revokeObjectURL(videoEditorBlobUrl);
    };
  }, [videoBlobUrl, videoEditorBlobUrl]);

  useEffect(() => {
    if (mode === 'video') {
      loadVideoHistory();
      loadVideoAnalytics();
      loadApiCredits();
    }
  }, [mode]);

  // Auto-poll every 8 seconds while any video is in 'processing' state
  useEffect(() => {
    if (mode !== 'video') return;
    const hasProcessing = videoHistory.some((v) => v.status === 'processing' || v.status === 'queued');
    if (!hasProcessing) return;
    const interval = setInterval(() => {
      loadVideoHistory();
    }, 8000);
    return () => clearInterval(interval);
  }, [mode, videoHistory]);

  // Poll /video/progress/{id} every 3s for the currently generating video
  useEffect(() => {
    if (!activeGenerationId) return;
    const poll = async () => {
      try {
        const prog = await api.getVideoProgress(activeGenerationId);
        setActiveGenerationProgress(prog);
        if (prog.status === 'success' || prog.status === 'failed') {
          if (prog.status === 'failed') {
            const failMessage = prog.message || 'Video generation failed.';
            setVideoError(failMessage);
            showDashboardToast(failMessage, 'error');
          }
          setActiveGenerationId(null);
          loadVideoHistory();
        }
      } catch {
        // ignore network errors during polling
      }
    };
    const interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, [activeGenerationId]);

  const filteredVideoHistory = videoHistory.filter((item) => {
    const search = videoHistorySearch.trim().toLowerCase();
    const title = String(item?.seo?.title || item?.run_id || `video ${item?.id || ''}`).toLowerCase();
    const desc = String(item?.seo?.description || '').toLowerCase();
    const matchesSearch = !search || title.includes(search) || desc.includes(search);
    const matchesStatus = videoHistoryStatus === 'all' || (item?.status || 'success') === videoHistoryStatus;
    return matchesSearch && matchesStatus;
  });

  const VIDEO_PAGE_SIZE = 5;
  const videoHistoryPageCount = Math.ceil(filteredVideoHistory.length / VIDEO_PAGE_SIZE);
  const pagedVideoHistory = filteredVideoHistory.slice(
    videoHistoryPage * VIDEO_PAGE_SIZE,
    (videoHistoryPage + 1) * VIDEO_PAGE_SIZE
  );

  return (
    <div className="max-w-4xl mx-auto px-4 py-4 md:p-8 space-y-4 md:space-y-8">
      <header className="flex flex-col sm:flex-row items-start justify-between gap-3 md:gap-4">
        <div>
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">{mode === 'video' ? 'AI Video Studio' : 'Generate Content'}</h2>
          <p className="text-[#A1A1AA] font-medium">
            {mode === 'video'
              ? 'Full-stack AI video creation — Claude plans your script, RunwayML Gen 4.5 renders cinematic scenes, storyboard previewer lets you approve every scene before render.'
              : 'Paste a URL or text. Get Twitter, LinkedIn, and TikTok content in 20 seconds.'}
          </p>
        </div>
        <a
          href="/demo"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 bg-transparent border-2 border-blue-500/30 hover:border-blue-500 hover:bg-blue-500/10 rounded-lg font-medium text-blue-400 transition-all whitespace-nowrap text-sm mt-1"
        >
          🎬 See Demo
        </a>
      </header>

      {mode !== 'video' && !workflowDismissed && (
        <div className="bg-[#18181B] border border-[#27272A] rounded-xl p-4 relative">
          <button
            onClick={() => { localStorage.setItem('tf_workflow_dismissed', '1'); setWorkflowDismissed(true); }}
            className="absolute top-3 right-3 p-1 text-[#52525B] hover:text-white transition-colors rounded"
            aria-label="Dismiss workflow guide"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <p className="text-[10px] font-bold text-[#52525B] uppercase tracking-widest mb-3 pr-6">How it works</p>
          <div className="flex items-start gap-1 overflow-x-auto pb-1">
            {[
              { icon: '🎤', title: 'Voice Learn', desc: 'Paste samples — AI learns your tone' },
              { icon: '⚡', title: 'Generate', desc: 'URL or text → 5 platforms in 20s' },
              { icon: '✏️', title: 'Edit & Refine', desc: 'Inline editor + hook A/B variations' },
              { icon: '📅', title: 'Schedule & Post', desc: 'Auto-post or email reminder' },
            ].map((item, i, arr) => (
              <React.Fragment key={item.title}>
                <div className="flex-shrink-0 flex flex-col items-center text-center w-28">
                  <div className="w-9 h-9 rounded-full bg-[#27272A] flex items-center justify-center text-lg mb-2">{item.icon}</div>
                  <p className="text-xs font-semibold text-white mb-0.5">{item.title}</p>
                  <p className="text-[10px] text-[#71717A] leading-snug">{item.desc}</p>
                </div>
                {i < arr.length - 1 && (
                  <div className="flex-shrink-0 flex items-center pt-3 px-1">
                    <svg className="w-4 h-4 text-[#3F3F46]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {mode !== 'video' && (
      <div className="bg-[#18181B] border border-[#27272A] rounded-2xl shadow-2xl overflow-hidden">
        {loading ? <LoadingState /> : (<>
        {/* Segmented Toggle */}
        <div style={{ display: 'flex', background: '#09090B', borderRadius: '14px', padding: '4px', gap: '4px', borderBottom: '1px solid #27272A' }}>
          <button
            onClick={() => { setInputType('url'); setContent(''); }}
            style={{
              flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              padding: '12px 16px', borderRadius: '10px', fontSize: '14px', fontWeight: '700',
              border: 'none', cursor: 'pointer', transition: 'all 0.15s',
              background: inputType === 'url' ? '#3B82F6' : 'transparent',
              color: inputType === 'url' ? 'white' : '#71717A',
              boxShadow: inputType === 'url' ? '0 4px 12px rgba(59,130,246,0.3)' : 'none',
            }}
          >
            <svg style={{ width: '16px', height: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
            Blog / Article URL
          </button>
          <button
            onClick={() => { setInputType('text'); setContent(''); }}
            style={{
              flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              padding: '12px 16px', borderRadius: '10px', fontSize: '14px', fontWeight: '700',
              border: 'none', cursor: 'pointer', transition: 'all 0.15s',
              background: inputType === 'text' ? '#3B82F6' : 'transparent',
              color: inputType === 'text' ? 'white' : '#71717A',
              boxShadow: inputType === 'text' ? '0 4px 12px rgba(59,130,246,0.3)' : 'none',
            }}
          >
            <svg style={{ width: '16px', height: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            Raw Text
          </button>
        </div>

        <div className="p-4 md:p-8 space-y-6">
          {/* Main Input */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-[#71717A] uppercase tracking-widest">
              {inputType === 'url' ? 'Paste Article or YouTube Link' : 'Your Content'}
            </label>
            {inputType === 'text' && !content && (
              <div className="flex flex-wrap gap-2 mb-1">
                <span className="text-[10px] font-bold text-[#52525B] uppercase tracking-widest self-center">Try an example:</span>
                {[
                  { label: '🍳 Recipe / Skill', text: '5 pasta mistakes home cooks make — and how to fix each one for restaurant-quality results every time' },
                  { label: '💪 Fitness tip', text: 'Why 80% of people quit their workout program in week 3, not week 1 — and the mindset shift that changes everything' },
                  { label: '💡 Business insight', text: 'I doubled my freelance rate without losing clients. Here\'s the exact conversation script I used to raise prices' },
                ].map((ex) => (
                  <button
                    key={ex.label}
                    onClick={() => setContent(ex.text)}
                    className="text-[11px] font-semibold bg-[#27272A] hover:bg-[#3B82F6]/20 border border-[#3F3F46] hover:border-[#3B82F6]/50 text-[#A1A1AA] hover:text-white px-3 py-1.5 rounded-lg transition-all"
                  >
                    {ex.label}
                  </button>
                ))}
              </div>
            )}
            {inputType === 'url' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '10px', marginBottom: '4px' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="#EF4444" style={{ flexShrink: 0 }}><path d="M21.8 8s-.2-1.4-.8-2c-.8-.8-1.6-.8-2-.9C16.6 5 12 5 12 5s-4.6 0-7 .1c-.4.1-1.2.1-2 .9-.6.6-.8 2-.8 2S2 9.6 2 11.2v1.5c0 1.6.2 3.2.2 3.2s.2 1.4.8 2c.8.8 1.8.8 2.3.9C6.8 19 12 19 12 19s4.6 0 7-.1c.4-.1 1.2-.1 2-.9.6-.6.8-2 .8-2s.2-1.6.2-3.2v-1.5C22 9.6 21.8 8 21.8 8zM10 15V9l5.5 3-5.5 3z"/></svg>
                <span style={{ fontSize: '12px', color: '#93C5FD' }}>YouTube URLs supported — transcript extracted automatically</span>
              </div>
            )}
            {inputType === 'url' ? (
              <div className="relative">
                <input
                  type="url"
                  placeholder="https://example.com/article  or  https://youtube.com/watch?v=..."
                  className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-4 pr-12 text-white focus:border-[#3B82F6] outline-none transition-all placeholder:text-[#52525B] font-medium"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  disabled={limitReached || atLimit}
                />
                {/* Clear Button */}
                {content && !limitReached && !atLimit && (
                  <button
                    onClick={() => setContent('')}
                    className="
                      absolute right-3 top-1/2 -translate-y-1/2
                      p-1.5 rounded-full
                      bg-gray-800 hover:bg-gray-700
                      text-gray-400 hover:text-gray-300
                      transition-colors
                    "
                    title="Clear"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            ) : (
              <div className="relative">
                <textarea
                  placeholder="Enter your content here (min 100 characters recommended)..."
                  className="w-full bg-[#09090B] border border-[#27272A] rounded-xl p-4 pr-12 text-white focus:border-[#3B82F6] outline-none transition-all h-40 resize-none placeholder:text-[#52525B] font-medium"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  disabled={limitReached || atLimit}
                />
                {/* Clear Button */}
                {content && !limitReached && !atLimit && (
                  <button
                    onClick={() => setContent('')}
                    className="
                      absolute right-3 top-3
                      p-1.5 rounded-full
                      bg-gray-800 hover:bg-gray-700
                      text-gray-400 hover:text-gray-300
                      transition-colors
                    "
                    title="Clear"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Platform Selection */}
            <div className="space-y-3 md:col-span-2">
              <label className="text-xs font-bold text-[#71717A] uppercase tracking-widest">Target Platforms</label>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  {id: 'twitter',  label: 'Twitter',  badgeColor: 'bg-[#1DA1F2]', activeClass: 'border-[#1DA1F2] bg-[#1DA1F2]/10 shadow-lg shadow-[#1DA1F2]/20',  inactiveClass: 'border-gray-700 bg-gray-800/50 hover:border-[#1DA1F2]/50 hover:bg-gray-800'},
                  {id: 'linkedin', label: 'LinkedIn', badgeColor: 'bg-[#0A66C2]', activeClass: 'border-[#0A66C2] bg-[#0A66C2]/10 shadow-lg shadow-[#0A66C2]/20', inactiveClass: 'border-gray-700 bg-gray-800/50 hover:border-[#0A66C2]/50 hover:bg-gray-800'},
                  {id: 'tiktok',   label: 'TikTok',   badgeColor: 'bg-pink-500',  activeClass: 'border-pink-500 bg-pink-500/10 shadow-lg shadow-pink-500/20',    inactiveClass: 'border-gray-700 bg-gray-800/50 hover:border-pink-500/50 hover:bg-gray-800'},
                  {id: 'reels',    label: 'Reels',    badgeColor: 'bg-purple-500',activeClass: 'border-purple-500 bg-purple-500/10 shadow-lg shadow-purple-500/20',inactiveClass: 'border-gray-700 bg-gray-800/50 hover:border-purple-500/50 hover:bg-gray-800'},
                  {id: 'shorts',   label: 'Shorts',   badgeColor: 'bg-red-500',   activeClass: 'border-red-500 bg-red-500/10 shadow-lg shadow-red-500/20',        inactiveClass: 'border-gray-700 bg-gray-800/50 hover:border-red-500/50 hover:bg-gray-800'},
                ].map(p => (
                  <button
                    key={p.id}
                    onClick={() => handleTogglePlatform(p.id)}
                    disabled={limitReached || atLimit}
                    className={`group relative p-4 rounded-xl border-2 transition-all flex flex-col items-center gap-2 ${
                      platforms.includes(p.id)
                        ? p.activeClass
                        : p.inactiveClass
                    }`}
                  >
                    <SocialPlatformIcon platform={p.id} className="w-7 h-7" />
                    <span className={`text-sm font-semibold ${platforms.includes(p.id) ? 'text-white' : 'text-[#A1A1AA]'}`}>{p.label}</span>
                    {platforms.includes(p.id) && (
                      <div className={`absolute -top-2 -right-2 w-6 h-6 ${p.badgeColor} rounded-full flex items-center justify-center shadow-lg`}>
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-xs font-bold text-[#71717A] uppercase tracking-widest">Tone</label>
              <div className="relative">
                <select
                  className="w-full appearance-none bg-[#09090B] border border-[#27272A] rounded-xl pl-4 pr-10 py-3 text-white focus:border-[#3B82F6] outline-none font-medium cursor-pointer disabled:opacity-50 transition-colors"
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  disabled={limitReached || atLimit}
                >
                  <option value="professional">Professional</option>
                  <option value="witty">Witty &amp; Viral</option>
                  <option value="educational">Educational</option>
                  <option value="controversial">Controversial</option>
                </select>
                <svg className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#52525B]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
              </div>
            </div>
          </div>

          {error && !genFailed && (
            <p className="text-red-400 text-sm font-semibold bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">{error}</p>
          )}

          {genFailed && (
            <div className="bg-red-500/5 border border-red-500/30 rounded-xl p-5 space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-lg">⚠️</span>
                <p className="text-red-400 font-bold text-sm">Generation Failed</p>
              </div>
              <p className="text-[#A1A1AA] text-sm">{error}</p>
              <p className="text-green-400 text-xs font-semibold">✓ Your credit was not deducted.</p>
              <button
                onClick={() => { setGenFailed(false); setError(''); handleGenerate(); }}
                className="px-4 py-2 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white text-sm font-bold rounded-lg transition-all"
              >
                Try Again →
              </button>
            </div>
          )}

          {(limitReached || (atLimit && plan === 'free')) ? (
            <div style={{
              background: '#18181B',
              border: '1px solid #3B82F6',
              borderRadius: '12px',
              padding: '32px',
              textAlign: 'center',
              marginTop: '16px'
            }}>
              <div style={{ fontSize: '40px', marginBottom: '16px' }}>⚡</div>
              <div style={{
                fontSize: '20px', fontWeight: '700', color: '#FAFAFA', marginBottom: '8px'
              }}>
                You have used all 5 free generations
              </div>
              <div style={{
                color: '#71717A', fontSize: '14px', marginBottom: '24px', lineHeight: '1.6'
              }}>
                Upgrade to Solo for unlimited generations,
                the in-app editor, and viral hook variations.
              </div>
              <div style={{
                display: 'flex', gap: '12px', justifyContent: 'center',
                marginBottom: '24px', flexWrap: 'wrap'
              }}>
                <div style={{
                  background: '#09090B', border: '1px solid #27272A',
                  borderRadius: '10px', padding: '20px 24px', minWidth: '160px'
                }}>
                  <div style={{ color: '#71717A', fontSize: '12px', marginBottom: '4px' }}>SOLO</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#FAFAFA' }}>$9</div>
                  <div style={{ color: '#71717A', fontSize: '12px', marginBottom: '12px' }}>/month</div>
                  <div style={{ color: '#A1A1AA', fontSize: '12px' }}>30 generations/mo</div>
                </div>
                <div style={{
                  background: '#09090B', border: '1px solid #3B82F6',
                  borderRadius: '10px', padding: '20px 24px', minWidth: '160px', position: 'relative'
                }}>
                  <div style={{
                    position: 'absolute', top: '-10px', left: '50%',
                    transform: 'translateX(-50%)', background: '#3B82F6',
                    color: 'white', fontSize: '10px', fontWeight: '700',
                    padding: '2px 10px', borderRadius: '20px'
                  }}>POPULAR</div>
                  <div style={{ color: '#71717A', fontSize: '12px', marginBottom: '4px' }}>FOUNDER</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#FAFAFA' }}>$19</div>
                  <div style={{ color: '#71717A', fontSize: '12px', marginBottom: '12px' }}>/month</div>
                  <div style={{ color: '#A1A1AA', fontSize: '12px' }}>100 generations/mo</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                <button
                  onClick={() => handleUpgrade('solo')}
                  disabled={!!checkoutLoading}
                  style={{
                    padding: '12px 24px', background: 'transparent',
                    border: '1px solid #3F3F46', borderRadius: '8px',
                    color: '#A1A1AA', fontSize: '14px', cursor: checkoutLoading ? 'not-allowed' : 'pointer',
                    fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px',
                    opacity: checkoutLoading && checkoutLoading !== 'solo' ? 0.5 : 1,
                  }}
                >
                  {checkoutLoading === 'solo' ? (
                    <><div style={{ width: '14px', height: '14px', border: '2px solid rgba(161,161,170,0.3)', borderTopColor: '#A1A1AA', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />Opening checkout...</>
                  ) : 'Upgrade to Solo →'}
                </button>
                <button
                  onClick={() => handleUpgrade('founder')}
                  disabled={!!checkoutLoading}
                  style={{
                    padding: '12px 24px', background: '#3B82F6',
                    border: 'none', borderRadius: '8px',
                    color: 'white', fontSize: '14px', cursor: checkoutLoading ? 'not-allowed' : 'pointer',
                    fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px',
                    opacity: checkoutLoading && checkoutLoading !== 'founder' ? 0.5 : 1,
                  }}
                >
                  {checkoutLoading === 'founder' ? (
                    <><div style={{ width: '14px', height: '14px', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />Opening checkout...</>
                  ) : 'Upgrade to Founder →'}
                </button>
              </div>
              <button
                onClick={() => setLimitReached(false)}
                style={{
                  marginTop: '16px', background: 'none', border: 'none',
                  color: '#60A5FA', fontSize: '14px', cursor: 'pointer', textDecoration: 'underline'
                }}
              >
                ← Go back
              </button>
            </div>
          ) : (
            <button
              onClick={handleGenerate}
              disabled={loading}
              style={{
                width: '100%', padding: '14px',
                background: loading ? '#1D4ED8' : '#3B82F6',
                color: 'white', border: 'none', borderRadius: '8px',
                fontSize: '16px', fontWeight: 700,
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                gap: '8px', transition: 'all 0.2s',
              }}
            >
              {loading ? (
                <>
                  <div style={{
                    width: '18px', height: '18px',
                    border: '2px solid rgba(255,255,255,0.3)',
                    borderTopColor: 'white', borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite',
                  }} />
                  Generating...
                </>
              ) : (
                `⚡ Generate Content — ${usageCount + 1} of ${usageLimit}`
              )}
            </button>
          )}
        </div>
        </>)}
      </div>
      )}

      {mode === 'video' && (
        <div className="bg-[#161B22] border border-[#30363D] rounded-2xl p-6 space-y-5">
          {/* Header row */}
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#1F6FEB]/25 to-purple-500/25 border border-[#1F6FEB]/30 flex items-center justify-center flex-shrink-0 shadow-lg shadow-[#1F6FEB]/10">
              <svg className="w-7 h-7 text-[#58A6FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1.5">
                <h3 className="text-white font-bold text-xl leading-none">AI Video Studio</h3>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase tracking-wider">Production</span>
              </div>
              <p className="text-[#8B949E] text-sm leading-relaxed">Claude plans your hook, body &amp; CTA with retention notes → storyboard previewer for scene-by-scene approval → RunwayML Gen 4.5 renders photorealistic clips → export-ready for TikTok, Reels &amp; Shorts.</p>
            </div>
          </div>

          {/* 3-step pipeline */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { icon: '🤖', step: '01', title: 'Claude Plans', desc: 'Hook, body & CTA with retention notes and platform SEO metadata' },
              { icon: '🎞️', step: '02', title: 'Preview & Approve', desc: 'Drag-and-drop storyboard — edit every scene before render' },
              { icon: '🎬', step: '03', title: 'RunwayML Renders', desc: 'Gen 4.5 AI video with characters, text overlays & auto captions' },
            ].map((s) => (
              <div key={s.step} className="p-3 rounded-xl bg-[#0D1117] border border-[#21262D]">
                <div className="text-lg mb-1.5">{s.icon}</div>
                <div className="text-[10px] font-bold text-[#484F58] uppercase tracking-wider mb-0.5">{s.step}</div>
                <div className="text-xs font-semibold text-[#E6EDF3] mb-1">{s.title}</div>
                <div className="text-[11px] text-[#8B949E] leading-snug">{s.desc}</div>
              </div>
            ))}
          </div>

          {/* Feature pills */}
          <div className="flex flex-wrap gap-2">
            {[
              '🎬 RunwayML Gen 4.5',
              '🤖 Claude Script Planner',
              '🎭 Character System',
              '🎞️ Storyboard Preview',
              '📱 TikTok · Reels · Shorts',
              '🔤 Auto Captions + SRT',
              '⚡ Batch Generation',
              '📊 SEO Optimizer',
            ].map(f => (
              <span key={f} className="text-xs px-3 py-1.5 bg-[#0D1117] border border-[#21262D] rounded-full text-[#8B949E]">{f}</span>
            ))}
          </div>

          <button
            onClick={openVideoModal}
            disabled={videoLoading}
            className="w-full px-4 py-4 rounded-xl bg-gradient-to-r from-[#1F6FEB] to-purple-600 hover:from-[#1a5ed4] hover:to-purple-700 text-white font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-[#1F6FEB]/20"
          >
            {videoLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Generating your video...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                Open Video Studio
              </>
            )}
          </button>
          {videoLoading && (
            <div className="flex items-center gap-2 text-xs text-[#8B949E] bg-[#0D1117] border border-[#21262D] rounded-xl px-4 py-3">
              <div className="w-1.5 h-1.5 rounded-full bg-[#1F6FEB] animate-pulse flex-shrink-0" />
              Generating... this usually takes <span className="text-[#C9D1D9] font-semibold mx-1">20–90 seconds</span>. Don't close this tab.
            </div>
          )}
        </div>
      )}

      {mode === 'video' && videoResult && (
        <div className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-white text-lg font-bold">
                {videoResult?.dry_run
                  ? 'Dry Run Complete ✅'
                  : videoBlobUrl
                  ? 'Video Ready ✅'
                  : 'Video Queued ✅'}
              </h3>
              <p className="text-[#71717A] text-sm">
                {videoResult?.dry_run
                  ? `${videoResult.duration_seconds || 0}s · simulation only (no MP4 rendered)`
                  : `${videoResult.duration_seconds || 0}s · vertical · image-first workflow`}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {videoBlobUrl && (
                <a
                  href={videoBlobUrl}
                  download={`${videoResult.run_id || 'ai_video'}.mp4`}
                  className="px-4 py-2 rounded-xl bg-[#3B82F6] hover:bg-[#2563EB] text-white text-sm font-bold flex items-center gap-1.5"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                  Download MP4
                </a>
              )}
              {videoResult.generation_id && (
                <button
                  onClick={() => openVideoEditor({
                    id: videoResult.generation_id,
                    video_url: videoResult.preview_url || videoResult.download_url,
                    thumbnail_url: videoResult.thumbnail_path
                      ? `/api/generate/video/thumbnail/${String(videoResult.thumbnail_path).split('/').pop()}`
                      : '',
                    seo: videoResult.seo || {},
                    platform_meta: videoResult.platform_meta || {},
                    editor: {},
                    status: videoResult.status || 'success',
                  }, { blobUrl: videoBlobUrl })}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold"
                >
                  Open Editor
                </button>
              )}
            </div>
          </div>

          {videoResult.status === 'queued' && (
            <div className="text-cyan-300 text-xs bg-cyan-500/10 border border-cyan-500/20 rounded-xl px-3 py-3">
              <div>
                {videoResult.message || 'Video generation has been queued in the background.'}
                {videoResult.dry_run
                  ? ' Dry-run mode is enabled: this validates workflow and stores history, but does not render/download a final MP4.'
                  : ''}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  onClick={loadVideoHistory}
                  className="px-3 py-1.5 rounded-lg bg-cyan-500/15 border border-cyan-400/30 text-cyan-200 hover:text-white"
                >
                  Refresh History
                </button>
                {videoResult.dry_run && (
                  <button
                    onClick={() => setShowVideoModal(true)}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-400/30 text-emerald-200 hover:text-white"
                  >
                    Open Studio (Render Real Video)
                  </button>
                )}
                <button
                  onClick={() => setShowVideoModal(true)}
                  className="px-3 py-1.5 rounded-lg border border-cyan-400/30 text-cyan-200 hover:text-white"
                >
                  Open Studio Again
                </button>
              </div>
            </div>
          )}

          {videoBlobUrl && (
            <div className="flex justify-center">
              <video controls src={videoBlobUrl} className="w-full max-w-[300px] rounded-xl border border-[#27272A] shadow-lg" />
            </div>
          )}

          {videoResult.warning && (
            <div className="text-amber-300 text-xs bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2">
              ⚠️ {videoResult.warning}
            </div>
          )}

          {videoResult.platform_meta && (
            <div className="p-4 rounded-xl bg-[#09090B] border border-[#27272A] space-y-3">
              <p className="text-[10px] font-bold text-[#71717A] uppercase tracking-widest">Platform Metadata</p>
              <div className="flex gap-2">
                {[
                  { key: 'youtube_shorts', label: 'YouTube Shorts' },
                  { key: 'reels', label: 'Reels' },
                  { key: 'tiktok', label: 'TikTok' },
                ].map(tab => (
                  <button
                    key={tab.key}
                    onClick={() => setVideoMetaTab(tab.key)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${videoMetaTab === tab.key ? 'bg-[#3B82F6] text-white' : 'bg-[#18181B] text-[#A1A1AA] border border-[#27272A]'}`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
              <div className="space-y-3 text-sm text-[#E4E4E7]">
                <div><span className="text-[10px] font-bold uppercase text-[#71717A]">Title</span><p className="mt-1">{videoResult.platform_meta?.[videoMetaTab]?.title || ''}</p></div>
                <div><span className="text-[10px] font-bold uppercase text-[#71717A]">Description</span><p className="mt-1 whitespace-pre-wrap text-[#A1A1AA] text-xs">{videoResult.platform_meta?.[videoMetaTab]?.description || ''}</p></div>
                <div><span className="text-[10px] font-bold uppercase text-[#71717A]">Hashtags</span><p className="mt-1 text-[#3B82F6] text-xs">{videoResult.platform_meta?.[videoMetaTab]?.hashtags || ''}</p></div>
              </div>
            </div>
          )}

          {videoResult.seo && (
            <div className="p-4 rounded-xl bg-[#09090B] border border-[#27272A] space-y-3">
              <p className="text-[10px] font-bold text-[#71717A] uppercase tracking-widest">YouTube SEO Metadata</p>
              <div className="space-y-2 text-sm text-[#E4E4E7]">
                <div>
                  <span className="text-[10px] font-bold uppercase text-[#71717A]">Title</span>
                  <p className="mt-1">{videoResult.seo.title || ''}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase text-[#71717A]">Description</span>
                  <p className="mt-1 whitespace-pre-wrap text-xs text-[#A1A1AA]">{videoResult.seo.description || ''}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase text-[#71717A]">Tags</span>
                  <p className="mt-1 text-xs">{Array.isArray(videoResult.seo.tags) ? videoResult.seo.tags.join(', ') : ''}</p>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase text-[#71717A]">Hashtags</span>
                  <p className="mt-1 text-[#3B82F6] text-xs">{Array.isArray(videoResult.seo.hashtags) ? videoResult.seo.hashtags.join(' ') : ''}</p>
                </div>
              </div>
            </div>
          )}

          {videoResult.costs && (
            <div className="p-4 rounded-xl bg-[#09090B] border border-[#27272A]">
              <p className="text-[10px] font-bold text-[#71717A] uppercase tracking-widest mb-2">Cost Tracking</p>
              <p className="text-xs text-[#A1A1AA]">Runway credits: {videoResult.costs.runway_credits_used || 0} · Total cost: ${Number(videoResult.costs.total_cost_usd || 0).toFixed(3)}</p>
            </div>
          )}
        </div>
      )}

      {mode === 'video' && (
      <div className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-bold">Recent Videos</h3>
          <button onClick={loadVideoHistory} className="text-xs px-3 py-1.5 rounded-lg border border-[#27272A] text-[#A1A1AA] hover:text-white hover:border-[#3F3F46] transition-colors">Refresh</button>
        </div>

          <div className="grid grid-cols-1 md:grid-cols-[minmax(0,1fr)_180px] gap-3">
          <input
            value={videoHistorySearch}
            onChange={(e) => { setVideoHistorySearch(e.target.value); setVideoHistoryPage(0); }}
            placeholder="Search by title or description"
            className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-3 py-2 text-white focus:border-[#3B82F6] outline-none text-sm"
          />
          <div className="relative">
            <select
              value={videoHistoryStatus}
              onChange={(e) => { setVideoHistoryStatus(e.target.value); setVideoHistoryPage(0); }}
              className="w-full appearance-none bg-[#09090B] border border-[#27272A] rounded-xl pl-3 pr-8 py-2 text-white focus:border-[#3B82F6] outline-none text-sm cursor-pointer"
            >
              <option value="all">All Statuses</option>
              <option value="success">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
            <svg className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#52525B]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
          </div>
        </div>

        {activeGenerationId && activeGenerationProgress && (
          <div className="mb-4 rounded-xl border border-[#3B82F6]/40 bg-[#0c1628] px-5 py-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#3B82F6] animate-pulse" />
                <span className="text-sm font-semibold text-white">
                  {activeGenerationProgress.status === 'success' ? 'Generation Complete!' :
                   activeGenerationProgress.status === 'failed' ? 'Generation Failed' :
                   'Generating Video...'}
                </span>
              </div>
              <span className="text-xs text-[#60A5FA] font-mono">
                {activeGenerationProgress.percent ?? 0}%
              </span>
            </div>
            <div className="w-full bg-[#1e293b] rounded-full h-2 mb-2">
              <div
                className="h-2 rounded-full transition-all duration-500"
                style={{
                  width: `${activeGenerationProgress.percent ?? 0}%`,
                  background: activeGenerationProgress.status === 'failed'
                    ? '#ef4444'
                    : activeGenerationProgress.status === 'success'
                    ? '#22c55e'
                    : 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                }}
              />
            </div>
            <p className="text-xs text-[#94A3B8] truncate">
              {activeGenerationProgress.message || 'Processing...'}
            </p>
          </div>
        )}

        {videoHistoryLoading ? (
          <div className="space-y-2">
            {[1,2,3].map(i => <div key={i} className="h-16 bg-[#09090B] rounded-xl border border-[#27272A] animate-pulse" />)}
          </div>
        ) : filteredVideoHistory.length === 0 ? (
          <div className="py-10 text-center">
            <div className="text-4xl mb-3">🎬</div>
            <p className="text-[#71717A] text-sm font-medium">No matching videos</p>
            <p className="text-[#52525B] text-xs mt-1">Try a different search term or status filter</p>
          </div>
        ) : (
          <div className="space-y-2">
            {pagedVideoHistory.map((item) => {
              const date = item.created_at ? new Date(item.created_at) : null;
              const now = new Date();
              const diffHours = date ? Math.floor((now - date) / 3600000) : null;
              const dateLabel = diffHours === null ? '' : diffHours < 1 ? 'Just now' : diffHours < 24 ? `${diffHours}h ago` : diffHours < 168 ? `${Math.floor(diffHours/24)}d ago` : date.toLocaleDateString();
              return (
                <div key={item.id} className="p-3 rounded-xl border border-[#27272A] bg-[#09090B] flex items-center gap-4">
                  <button
                    onClick={() => openVideoEditor(item)}
                    className="relative w-24 h-16 rounded-lg overflow-hidden bg-gradient-to-br from-[#3B82F6]/20 to-purple-500/20 border border-[#27272A] flex items-center justify-center flex-shrink-0 group"
                  >
                    {item.thumbnail_url ? (
                      <img
                        src={item.thumbnail_url}
                        alt=""
                        className="w-full h-full object-cover"
                        onError={(e) => { e.currentTarget.style.display = 'none'; }}
                      />
                    ) : null}
                    <div className="absolute inset-0 flex items-center justify-center opacity-80 group-hover:opacity-100 transition-opacity">
                      <svg className="w-6 h-6 text-[#3B82F6]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    </div>
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                      <p className="text-sm text-[#E4E4E7] font-medium truncate">{item.seo?.title || item.run_id || `Video ${item.id}`}</p>
                      {(item.status === 'processing' || item.status === 'queued') && (
                        <span className="flex-shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/25">
                          {item.status === 'queued' ? 'QUEUED' : 'PROCESSING'}
                        </span>
                      )}
                      {item.status === 'failed' && <span className="flex-shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-red-500/15 text-red-300 border border-red-500/25">FAILED</span>}
                      {(item.status === 'success' || item.status === 'completed') && (
                        <>
                          <span className="flex-shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">DONE</span>
                          {item.warning && item.warning.includes('Dry-run') && <span className="flex-shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-sky-500/15 text-sky-300 border border-sky-500/25">DRY RUN</span>}
                        </>
                      )}
                    </div>
                    <p className="text-xs text-[#71717A]">{item.duration_seconds ? `${item.duration_seconds}s` : ''}{item.duration_seconds && dateLabel ? ' · ' : ''}{dateLabel}{item.costs?.runway_credits_used > 0 ? ` · ${item.costs.runway_credits_used} cr` : ''}</p>
                    <p className="text-xs text-[#8B97B3] truncate mt-1">
                      {item.status === 'failed' ? (item.warning || 'Generation failed') : (item.seo?.thumbnail_text || item.seo?.description || 'Saved metadata available')}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      className="text-xs px-3 py-1.5 rounded-lg border border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 hover:text-white transition-colors"
                      onClick={() => openVideoStudioFromHistory(item)}
                    >
                      Reuse in Studio
                    </button>
                    <button
                      className="text-xs px-3 py-1.5 rounded-lg border border-[#3B82F6]/30 bg-[#3B82F6]/10 hover:bg-[#3B82F6]/20 text-[#8DC0FF] hover:text-white transition-colors"
                      onClick={() => openVideoEditor(item)}
                    >
                      View / Edit
                    </button>
                    {item.status === 'failed' && (
                      <button
                        className="text-xs px-3 py-1.5 rounded-lg border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-red-300 hover:text-white transition-colors"
                        onClick={() => openVideoStudioFromHistory(item)}
                        title="Open in Studio to retry"
                      >
                        ↺ Retry
                      </button>
                    )}
                    {(item.status === 'processing' || item.status === 'queued') && (
                      <div className="flex flex-col items-end gap-1">
                        {activeGenerationId === item.id && activeGenerationProgress ? (
                          <>
                            <div className="w-20 bg-[#1e293b] rounded-full h-1.5">
                              <div
                                className="h-1.5 rounded-full transition-all duration-500"
                                style={{
                                  width: `${activeGenerationProgress.percent ?? 0}%`,
                                  background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
                                }}
                              />
                            </div>
                            <span className="text-[9px] text-amber-300">{activeGenerationProgress.percent ?? 0}%</span>
                          </>
                        ) : (
                          <span className="text-xs px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-300 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" /> In progress
                          </span>
                        )}
                      </div>
                    )}
                    {(item.status !== 'processing' && item.status !== 'queued') && (
                      <button
                        className="text-xs px-3 py-1.5 rounded-lg border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-red-300 hover:text-white transition-colors disabled:opacity-50"
                        onClick={() => handleDeleteVideoHistoryItem(item)}
                        disabled={deletingVideoId === item.id}
                        title="Delete this video and related assets"
                      >
                        {deletingVideoId === item.id ? 'Deleting...' : 'Delete'}
                      </button>
                    )}
                    {item.download_url && (item.status === 'success' || item.status === 'completed') && (
                      <button
                        className="text-xs px-3 py-1.5 rounded-lg bg-[#27272A] hover:bg-[#3F3F46] text-[#A1A1AA] hover:text-white transition-colors flex items-center gap-1"
                        onClick={() => downloadHistoryVideo(item.download_url, `${item.run_id || 'video'}.mp4`)}
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                        Download
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {!videoHistoryLoading && filteredVideoHistory.length > VIDEO_PAGE_SIZE && (
          <div className="flex items-center justify-between pt-2 border-t border-[#27272A]">
            <p className="text-xs text-[#484F58]">
              {videoHistoryPage * VIDEO_PAGE_SIZE + 1}–{Math.min((videoHistoryPage + 1) * VIDEO_PAGE_SIZE, filteredVideoHistory.length)} of {filteredVideoHistory.length} videos
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setVideoHistoryPage(0)}
                disabled={videoHistoryPage === 0}
                className="h-7 w-7 flex items-center justify-center rounded-lg text-[#8B949E] hover:text-white hover:bg-[#21262D] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="First page"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" /></svg>
              </button>
              <button
                onClick={() => setVideoHistoryPage(p => Math.max(0, p - 1))}
                disabled={videoHistoryPage === 0}
                className="h-7 w-7 flex items-center justify-center rounded-lg text-[#8B949E] hover:text-white hover:bg-[#21262D] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="Previous page"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              </button>
              {Array.from({ length: videoHistoryPageCount }, (_, i) => i).map((i) => (
                <button
                  key={i}
                  onClick={() => setVideoHistoryPage(i)}
                  className={`h-7 min-w-[28px] px-1 rounded-lg text-xs font-semibold transition-colors ${
                    i === videoHistoryPage
                      ? 'bg-[#1F6FEB] text-white'
                      : 'text-[#8B949E] hover:text-white hover:bg-[#21262D]'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setVideoHistoryPage(p => Math.min(videoHistoryPageCount - 1, p + 1))}
                disabled={videoHistoryPage >= videoHistoryPageCount - 1}
                className="h-7 w-7 flex items-center justify-center rounded-lg text-[#8B949E] hover:text-white hover:bg-[#21262D] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="Next page"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              </button>
              <button
                onClick={() => setVideoHistoryPage(videoHistoryPageCount - 1)}
                disabled={videoHistoryPage >= videoHistoryPageCount - 1}
                className="h-7 w-7 flex items-center justify-center rounded-lg text-[#8B949E] hover:text-white hover:bg-[#21262D] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title="Last page"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>
              </button>
            </div>
          </div>
        )}
      </div>
      )}

      {mode === 'video' && (
        <div className="bg-[#0D1117] border border-[#21262D] rounded-2xl p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-white font-bold">Analytics</h3>
              <p className="text-xs text-[#8B949E] mt-0.5">Runway usage &amp; per-video performance</p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => { loadApiCredits(); loadVideoAnalytics(); }} className="text-xs px-3 py-1.5 rounded-lg border border-[#30363D] text-[#8B949E] hover:text-white hover:border-[#484F58] transition-colors">↺ Refresh</button>
            </div>
          </div>

          {/* Live API Credit Balances */}
          <div className="rounded-xl border border-[#21262D] bg-[#161B22] p-4 space-y-3">
            <p className="text-[10px] text-[#8B949E] uppercase tracking-widest font-bold">Live API Balances</p>
            {apiCreditsLoading ? (
              <p className="text-xs text-[#71717A]">Fetching balances…</p>
            ) : apiCredits ? (
              <div className="space-y-3">
                {/* Runway ML */}
                {(() => {
                  const r = apiCredits.runway || {};
                  const bal = r.ok ? Number(r.balance ?? 0) : null;
                  const cap = 1000; // display scale reference
                  const pct = bal !== null ? Math.min(100, Math.round((bal / cap) * 100)) : 0;
                  return (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] text-[#8B949E] flex items-center gap-1.5">
                          <span className="text-base">🎬</span> Runway ML
                        </span>
                        <span className={`text-xs font-semibold ${r.ok ? 'text-[#60CDFF]' : 'text-[#484F58]'}`}>
                          {r.ok ? `${bal?.toLocaleString() ?? '—'} cr` : (r.error || '—')}
                        </span>
                      </div>
                      {r.ok && (
                        <div className="h-1.5 rounded-full bg-[#21262D] overflow-hidden">
                          <div className="h-full rounded-full bg-[#60CDFF]" style={{ width: `${pct}%` }} />
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* ElevenLabs */}
                {(() => {
                  const e = apiCredits.elevenlabs || {};
                  const used = e.ok ? Number(e.used ?? 0) : null;
                  const limit = e.ok ? Number(e.limit ?? 0) : null;
                  const remaining = e.ok ? Number(e.remaining ?? 0) : null;
                  const pct = (e.ok && limit > 0) ? Math.min(100, Math.round(((limit - used) / limit) * 100)) : 0;
                  return (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] text-[#8B949E] flex items-center gap-1.5">
                          <span className="text-base">🔊</span> ElevenLabs
                        </span>
                        <span className={`text-xs font-semibold ${e.ok ? 'text-purple-400' : 'text-[#484F58]'}`}>
                          {e.ok
                            ? `${remaining?.toLocaleString() ?? '—'} / ${limit?.toLocaleString() ?? '—'} chars`
                            : (e.error || '—')}
                        </span>
                      </div>
                      {e.ok && limit > 0 && (
                        <div className="h-1.5 rounded-full bg-[#21262D] overflow-hidden">
                          <div className="h-full rounded-full bg-purple-500" style={{ width: `${pct}%` }} />
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* Gemini */}
                {(() => {
                  const g = apiCredits.gemini || {};
                  const used = g.ok ? Number(g.used_today ?? 0) : null;
                  const quota = g.ok ? Number(g.daily_quota ?? 500) : null;
                  const pct = (g.ok && quota > 0) ? Math.min(100, Math.round((used / quota) * 100)) : 0;
                  return (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] text-[#8B949E] flex items-center gap-1.5">
                          <span className="text-base">✨</span> Gemini Images
                        </span>
                        <span className={`text-xs font-semibold ${g.ok ? 'text-emerald-400' : 'text-[#484F58]'}`}>
                          {g.ok ? `${used?.toLocaleString() ?? 0} / ${quota?.toLocaleString() ?? 500} today` : (g.error || '—')}
                        </span>
                      </div>
                      {g.ok && quota > 0 && (
                        <div className="h-1.5 rounded-full bg-[#21262D] overflow-hidden">
                          <div className="h-full rounded-full bg-emerald-500" style={{ width: `${pct}%` }} />
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* HuggingFace */}
                {(() => {
                  const hf = apiCredits.huggingface || {};
                  return (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] text-[#8B949E] flex items-center gap-1.5">
                          <span className="text-base">⚡</span> HuggingFace
                        </span>
                        <span className={`text-xs font-semibold ${hf.ok ? 'text-sky-400' : 'text-[#484F58]'}`}>
                          {hf.ok ? `✓ Token OK${hf.username ? ` · @${hf.username}` : ''}` : (hf.error || '—')}
                        </span>
                      </div>
                      {hf.ok && hf.model && (
                        <div className="text-[10px] text-[#484F58] mt-0.5">Model: {hf.model}</div>
                      )}
                    </div>
                  );
                })()}
              </div>
            ) : (
              <p className="text-xs text-[#484F58]">Could not fetch balances. Check API keys.</p>
            )}
          </div>
          {videoAnalyticsLoading ? (
            <div className="text-sm text-[#71717A]">Loading analytics...</div>
          ) : videoAnalytics ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[{
                  label: 'Total Videos', value: videoAnalytics.totalVideos || 0, valueClass: 'text-white', icon: '🎬',
                },{
                  label: 'Credits Used', value: Number(videoAnalytics.runwayCreditsUsed || 0).toFixed(1), valueClass: 'text-amber-300', icon: '⚡',
                },{
                  label: 'Avg Cost', value: `$${Number(videoAnalytics.avgCostPerVideo || 0).toFixed(3)}`, valueClass: 'text-[#60CDFF]', icon: '💰',
                },{
                  label: 'Credits Left', value: (() => {
                    const apibal = apiCredits?.runway?.ok ? Number(apiCredits.runway.balance ?? 0) : null;
                    if (apibal !== null) return apibal.toFixed(0);
                    return Math.max(0, 750 - Number(videoAnalytics.runwayCreditsUsed || 0)).toFixed(0);
                  })(), valueClass: 'text-emerald-400', icon: '✦',
                }].map(stat => (
                  <div key={stat.label} className="p-4 rounded-xl bg-[#161B22] border border-[#21262D] flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] text-[#8B949E] uppercase tracking-widest font-bold">{stat.label}</p>
                      <span className="text-base">{stat.icon}</span>
                    </div>
                    <p className={`text-2xl font-bold ${stat.valueClass}`}>{stat.value}</p>
                  </div>
                ))}
              </div>

              {/* Table */}
              {(() => {
                const rows = (videoAnalytics.recentVideos || []);
                const visible = analyticsHideZero ? rows.filter(v => Number(v.runwayCredits || 0) > 0 || Number(v.views || 0) > 0) : rows;
                return (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-xs text-[#8B949E]">{visible.length} of {rows.length} videos</p>
                      <button
                        onClick={() => setAnalyticsHideZero(h => !h)}
                        className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                          analyticsHideZero ? 'border-[#388bfd]/40 bg-[#388bfd]/10 text-[#388bfd]' : 'border-[#30363D] text-[#8B949E] hover:text-white'
                        }`}
                      >
                        {analyticsHideZero ? '◉' : '○'} {analyticsHideZero ? 'Hiding zero-activity rows' : 'Show all rows'}
                      </button>
                    </div>
                    <div className="overflow-auto border border-[#21262D] rounded-xl">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-left text-[#8B949E] border-b border-[#21262D] bg-[#161B22]">
                            <th className="px-3 py-2.5 font-semibold">Title</th>
                            <th className="px-3 py-2.5 font-semibold text-right">Duration</th>
                            <th className="px-3 py-2.5 font-semibold text-right">Credits</th>
                            <th className="px-3 py-2.5 font-semibold text-right">Cost</th>
                            <th className="px-3 py-2.5 font-semibold text-right">Views</th>
                            <th className="px-3 py-2.5 font-semibold text-right">ROI</th>
                          </tr>
                        </thead>
                        <tbody>
                          {visible.length === 0 && (
                            <tr><td colSpan={6} className="px-3 py-6 text-center text-[#484F58] text-xs">No videos with activity yet</td></tr>
                          )}
                          {visible.map((v) => (
                            <tr key={v.id} className="border-b border-[#161B22] hover:bg-[#161B22] transition-colors text-[#C9D1D9]">
                              <td className="px-3 py-2 max-w-[200px] truncate">{v.title || `Video ${v.id}`}</td>
                              <td className="px-3 py-2 text-right text-[#8B949E]">{v.duration || 0}s</td>
                              <td className="px-3 py-2 text-right">
                                <span className={Number(v.runwayCredits || 0) > 0 ? 'text-amber-300 font-semibold' : 'text-[#484F58]'}>{Number(v.runwayCredits || 0).toFixed(1)}</span>
                              </td>
                              <td className="px-3 py-2 text-right">
                                <span className={Number(v.totalCost || 0) > 0 ? 'text-[#60CDFF]' : 'text-[#484F58]'}>${Number(v.totalCost || 0).toFixed(3)}</span>
                              </td>
                              <td className="px-3 py-2 text-right text-[#8B949E]">{v.views || 0}</td>
                              <td className="px-3 py-2 text-right text-[#8B949E]">{v.roi != null ? `${v.roi}x` : '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                );
              })()}
            </>
          ) : (
            <div className="py-8 text-center">
              <div className="text-3xl mb-2">📊</div>
              <p className="text-sm text-[#8B949E]">No analytics data yet. Generate your first video to see stats here.</p>
            </div>
          )}
        </div>
      )}

      {mode === 'video' && (
        <div className="bg-[#0D1117] border border-[#21262D] rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-white font-bold">Batch Generation</h3>
              <p className="text-xs text-[#8B949E] mt-0.5">Queue multiple topics at once. Jobs run in the background.</p>
            </div>
          </div>

          {/* Topic input */}
          <div className="space-y-2">
            <div className="relative">
              <textarea
                value={batchTopics}
                onChange={(e) => setBatchTopics(e.target.value)}
                placeholder="Enter one topic per line, e.g.:\n5 ways to boost productivity\nHow to grow on TikTok in 2026"
                className="w-full bg-[#161B22] border border-[#21262D] focus:border-[#388bfd] rounded-xl p-4 text-sm text-[#E6EDF3] placeholder:text-[#484F58] outline-none resize-none h-28 transition-colors"
              />
              {batchTopics.trim() && (
                <div className="absolute bottom-3 right-3 flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded-full bg-[#21262D] border border-[#30363D] text-[10px] font-bold text-[#8B949E]">
                    {batchTopics.trim().split('\n').filter(l => l.trim()).length} topic{batchTopics.trim().split('\n').filter(l => l.trim()).length !== 1 ? 's' : ''}
                  </span>
                  <button
                    onClick={() => setBatchTopics('')}
                    className="text-[10px] text-[#484F58] hover:text-red-400 transition-colors"
                  >✕ Clear</button>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleBatchGenerate}
              disabled={batchLoading || !batchTopics.trim()}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#1F6FEB] hover:bg-[#388bfd] text-white text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {batchLoading ? (
                <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Queueing...</>
              ) : (
                <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg> Queue Batch</>
              )}
            </button>
            <button
              onClick={refreshBatchStatus}
              disabled={!batchResult?.batch_id || batchStatusLoading}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-[#30363D] text-[#8B949E] hover:text-white hover:border-[#484F58] text-sm font-semibold disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              {batchStatusLoading ? 'Refreshing...' : '↺ Refresh Status'}
            </button>
          </div>

          {batchResult?.batch_id && (
            <div className="rounded-xl border border-[#21262D] bg-[#161B22] p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-xs text-[#8B949E] font-mono">Batch: {batchResult.batch_id}</div>
                {batchResult.completed === batchResult.total_videos && batchResult.total_videos > 0 && (
                  <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">COMPLETE</span>
                )}
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="text-center p-2 rounded-lg bg-[#0D1117]">
                  <div className="text-lg font-bold text-[#388bfd]">{batchResult.total_videos ?? batchResult.total ?? 0}</div>
                  <div className="text-[10px] text-[#484F58] uppercase">Total</div>
                </div>
                <div className="text-center p-2 rounded-lg bg-[#0D1117]">
                  <div className="text-lg font-bold text-emerald-400">{batchResult.completed ?? 0}</div>
                  <div className="text-[10px] text-[#484F58] uppercase">Done</div>
                </div>
                <div className="text-center p-2 rounded-lg bg-[#0D1117]">
                  <div className="text-lg font-bold text-red-400">{batchResult.failed ?? 0}</div>
                  <div className="text-[10px] text-[#484F58] uppercase">Failed</div>
                </div>
              </div>
              {(batchResult.processing ?? 0) > 0 && (
                <div className="flex items-center gap-2 text-xs text-amber-300">
                  <div className="w-3 h-3 border-2 border-amber-300/30 border-t-amber-300 rounded-full animate-spin" />
                  {batchResult.processing} job{batchResult.processing !== 1 ? 's' : ''} processing...
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Post-gen CTA bar */}
      {mode !== 'video' && output && (
        <div className="bg-[#18181B] border border-[#3B82F6]/30 rounded-2xl p-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2.5 flex-1 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-white leading-none">Content ready!</p>
              <p className="text-xs text-[#71717A] mt-0.5">Pick your next step</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => window.dispatchEvent(new CustomEvent('dashboard-change-tab', { detail: 'calendar' }))}
              className="flex items-center gap-1.5 px-3 py-2 bg-[#09090B] border border-[#27272A] hover:border-[#3F3F46] text-[#A1A1AA] hover:text-white text-xs font-semibold rounded-lg transition-all"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              Schedule Posts
            </button>
            {(output['tiktok'] || reelsMeta || shortsMeta) && (
              <button
                onClick={() => {
                  const script = output['tiktok'] || reelsMeta?.description || shortsMeta?.description || '';
                  openVideoModalWithScript(script);
                }}
                className="flex items-center gap-1.5 px-3 py-2 bg-[#3B82F6]/10 border border-[#3B82F6]/30 hover:bg-[#3B82F6]/20 text-[#3B82F6] text-xs font-semibold rounded-lg transition-all"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                Create AI Video
              </button>
            )}
          </div>
        </div>
      )}

      {/* Output Results */}
      {mode !== 'video' && output && (
        <div className="bg-[#18181B] border border-[#27272A] rounded-2xl overflow-hidden">
          {/* YouTube video info banner */}
          {videoMetadata && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', background: 'rgba(239,68,68,0.07)', borderBottom: '1px solid rgba(239,68,68,0.2)' }}>
              {videoMetadata.thumbnail_url && (
                <img src={videoMetadata.thumbnail_url} alt="" style={{ width: '80px', height: '50px', objectFit: 'cover', borderRadius: '6px', flexShrink: 0 }} />
              )}
              <div style={{ minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="#EF4444"><path d="M21.8 8s-.2-1.4-.8-2c-.8-.8-1.6-.8-2-.9C16.6 5 12 5 12 5s-4.6 0-7 .1c-.4.1-1.2.1-2 .9C2.4 6.6 2.2 8 2.2 8S2 9.6 2 11.2v1.5c0 1.6.2 3.2.2 3.2s.2 1.4.8 2c.8.8 1.8.8 2.3.9C6.8 19 12 19 12 19s4.6 0 7-.1c.4-.1 1.2-.1 2-.9.6-.6.8-2 .8-2s.2-1.6.2-3.2v-1.5C22 9.6 21.8 8 21.8 8zM10 15V9l5.5 3-5.5 3z"/></svg>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: '#EF4444', textTransform: 'uppercase', letterSpacing: '0.05em' }}>YouTube</span>
                </div>
                {videoMetadata.title && (
                  <p style={{ color: '#E4E4E7', fontWeight: 600, fontSize: '13px', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{videoMetadata.title}</p>
                )}
                {videoMetadata.channel && (
                  <p style={{ color: '#71717A', fontSize: '11px', margin: '2px 0 0' }}>{videoMetadata.channel}</p>
                )}
              </div>
            </div>
          )}
          <div className="flex border-b border-[#27272A] p-2 gap-1 overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
            {platforms.filter(p => output[p]).map(p => (
              <button
                key={p}
                onClick={() => setActiveTab(p)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === p ? 'bg-[#3B82F6] text-white' : 'text-[#71717A] hover:text-white'
                }`}
              >
                <SocialPlatformIcon platform={p} className="w-4 h-4" />
                {PLATFORM_LABELS[p]}
              </button>
            ))}
            {reelsMeta && (
              <button
                onClick={() => setActiveTab('reels')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === 'reels' ? 'bg-pink-500/20 text-pink-400' : 'text-[#71717A] hover:text-white'
                }`}
              >
                <SocialPlatformIcon platform="reels" className="w-4 h-4" />
                {PLATFORM_LABELS.reels}
              </button>
            )}
            {shortsMeta && (
              <button
                onClick={() => setActiveTab('shorts')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === 'shorts' ? 'bg-red-500/20 text-red-400' : 'text-[#71717A] hover:text-white'
                }`}
              >
                <SocialPlatformIcon platform="shorts" className="w-4 h-4" />
                {PLATFORM_LABELS.shorts}
              </button>
            )}
          </div>
          <div className="p-6">
            {platforms.filter(p => output[p]).map(p => (
              <div key={p} style={{ display: activeTab === p ? 'block' : 'none' }}>
                {hookVariations?.[p]?.length > 0 && (
                  <HookVariationsPanel
                    variations={hookVariations[p]}
                    onUseHook={(hook) => handleHookSelect(p, hook)}
                  />
                )}
                <EditableOutput
                  key={`${currentGenerationId}-${p}-${hookVersions[p] || 0}`}
                  platform={p}
                  content={output[p]}
                  generationId={currentGenerationId}
                />
                {p === 'tiktok' && (
                  <button
                    onClick={() => openVideoModalWithScript(output['tiktok'])}
                    className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#3B82F6]/10 border border-[#3B82F6]/30 hover:bg-[#3B82F6]/20 text-[#3B82F6] text-sm font-semibold rounded-xl transition-all"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                    Generate AI Video from this Script
                  </button>
                )}
              </div>
            ))}
            {reelsMeta && (
              <div style={{ display: activeTab === 'reels' ? 'block' : 'none' }}>
                <ReelsMetadataOutput
                  meta={reelsMeta}
                  generationId={currentGenerationId}
                  hookVariations={hookVariations?.reels}
                  onHookSelect={handleHookSelect}
                  hookTitleVersion={hookVersions.reels || 0}
                />
                <button
                  onClick={() => openVideoModalWithScript(reelsMeta.description || '')}
                  className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 bg-pink-500/10 border border-pink-500/30 hover:bg-pink-500/20 text-pink-400 text-sm font-semibold rounded-xl transition-all"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                  Generate AI Video from this Reel Script
                </button>
              </div>
            )}
            {shortsMeta && (
              <div style={{ display: activeTab === 'shorts' ? 'block' : 'none' }}>
                <ShortsMetadataOutput
                  meta={shortsMeta}
                  generationId={currentGenerationId}
                  hookVariations={hookVariations?.shorts}
                  onHookSelect={handleHookSelect}
                  hookTitleVersion={hookVersions.shorts || 0}
                />
                <button
                  onClick={() => openVideoModalWithScript(shortsMeta.description || '')}
                  className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 text-red-400 text-sm font-semibold rounded-xl transition-all"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                  Generate AI Video from this Short Script
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {showVideoEditor && selectedVideoEditorItem?.id && (
        <div className="fixed inset-0 z-[10000] bg-[#010409] flex flex-col">
          <div className="border-b border-[#21262D] bg-[#0D1117] px-6 py-3 flex items-center justify-between flex-shrink-0">
            <div>
              <h3 className="text-white font-bold text-base">Video Asset Editor</h3>
              <p className="text-xs text-[#8B949E] mt-0.5">
                {selectedVideoEditorItem?.seo?.title || 'Untitled video'}
              </p>
            </div>
            <button
              onClick={() => {
                setShowVideoEditor(false);
                setSelectedVideoEditorItem(null);
              }}
              className="h-9 w-9 rounded-full bg-[#161B22] border border-[#30363D] text-[#8B949E] hover:text-white hover:border-[#484F58] transition-colors flex items-center justify-center"
              aria-label="Close editor"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 min-h-0 overflow-hidden">
            <VideoEditor
              video={{
                id: selectedVideoEditorItem.id,
                video_url: videoEditorBlobUrl,
                thumbnail_url: selectedVideoEditorItem.thumbnail_url || '',
                seo_title: selectedVideoEditorItem?.seo?.title || '',
                seo: selectedVideoEditorItem?.seo || {},
                platform_meta: selectedVideoEditorItem?.platform_meta || {},
                editor: selectedVideoEditorItem?.editor || {},
                captions: selectedVideoEditorItem?.editor?.captions || [],
                status: selectedVideoEditorItem?.status,
              }}
              onSave={handleSaveVideoEditor}
            />
          </div>
        </div>
      )}

      <AIVideoModal
        open={showVideoModal}
        onClose={() => setShowVideoModal(false)}
        onGeneratePlan={handleGenerateVideoPlan}
        onGeneratePreview={handleGenerateVideoPreview}
        onGenerateVideo={handleGenerateVideo}
        loading={videoLoading}
        planning={videoPlanning}
        form={videoForm}
        setForm={setVideoForm}
        scriptState={videoScriptState}
        onScriptStateChange={syncVideoScriptState}
        scriptModified={videoScriptModified}
        error={videoError}
        plan={videoPlan}
        planError={videoPlanError}
        preview={videoPreview}
        previewScenes={previewScenes}
        setPreviewScenes={setPreviewScenes}
        characterPresets={characterPresets}
        videoMode={videoMode}
        onRegeneratePlanFromEdits={handleRegeneratePlanFromEdits}
        onClearPreview={() => { setVideoPreview(null); setPreviewScenes([]); }}
        onStartFresh={() => { resetVideoModal(); }}
      />

      {/* Embedded Checkout Modal */}
      {showCheckoutModal && (
        <StripeCheckoutModal
          clientSecret={checkoutClientSecret}
          onClose={handleCloseCheckout}
        />
      )}

      {/* Help Chatbot */}
      <HelpChatbot />
    </div>
  );
}
