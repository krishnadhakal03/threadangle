import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { useConnectedAccounts } from '../hooks/useConnectedAccounts';
import AutoPostScheduler from './AutoPostScheduler';

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };
  return (
    <button
      onClick={handleCopy}
      className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
        copied ? 'bg-green-500/20 text-green-400' : 'bg-[#27272A] text-[#A1A1AA] hover:text-white'
      }`}
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

function PlatformSection({ label, output, editedOutput }) {
  const raw = editedOutput || output;
  if (!raw) return null;
  const items = Array.isArray(raw) ? raw : [raw];
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <p className="text-xs font-bold text-[#71717A] uppercase tracking-wider">{label}</p>
        {editedOutput && (
          <span className="flex items-center gap-1 text-[10px] font-semibold text-purple-400 bg-purple-500/10 border border-purple-500/20 px-1.5 py-0.5 rounded">
            <svg className="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
            </svg>
            edited
          </span>
        )}
      </div>
      {items.map((item, i) => {
        const text = typeof item === 'string' ? item : item?.text || JSON.stringify(item);
        return (
          <div key={i} className="bg-[#09090B] rounded-xl p-4 flex items-start gap-3">
            <p className="text-[#E4E4E7] text-sm leading-relaxed flex-1 whitespace-pre-wrap">{text}</p>
            <CopyButton text={text} />
          </div>
        );
      })}
    </div>
  );
}

function HistoryCard({ item, onSchedule, onAutoPost, getFriendlyErrorMessage }) {
  const [expanded, setExpanded] = useState(false);
  const platforms = [
    item.twitter_output && 'Twitter / X',
    item.linkedin_output && 'LinkedIn',
    item.tiktok_output && 'TikTok',
  ].filter(Boolean);

  // Build a quick preview snippet from the first available output
  const getPreviewSnippet = () => {
    const raw = item.twitter_content_edited || item.twitter_output || item.linkedin_content_edited || item.linkedin_output || item.tiktok_content_edited || item.tiktok_output;
    if (!raw) return null;
    let text;
    if (Array.isArray(raw)) {
      const first = raw[0];
      text = typeof first === 'string' ? first : (first?.text || first?.content || '');
    } else if (typeof raw === 'string') {
      text = raw;
    } else if (raw && typeof raw === 'object') {
      text = raw.text || raw.content || raw.description || '';
    } else {
      return null;
    }
    if (!text || typeof text !== 'string') return null;
    const clean = text.replace(/\n+/g, ' ').trim();
    return clean.length > 110 ? clean.slice(0, 107) + '…' : clean;
  };
  const preview = item.status !== 'failed' ? getPreviewSnippet() : null;

  // Quick copy the best available first-platform output
  const [quickCopied, setQuickCopied] = useState(false);
  const handleQuickCopy = (e) => {
    e.stopPropagation();
    const raw = item.twitter_content_edited || item.twitter_output || item.linkedin_content_edited || item.linkedin_output;
    if (!raw) return;
    const text = Array.isArray(raw) ? raw.map(t => typeof t === 'string' ? t : t?.text || '').join('\n\n') : String(raw);
    navigator.clipboard.writeText(text).then(() => {
      setQuickCopied(true);
      setTimeout(() => setQuickCopied(false), 2000);
    });
  };

  const formattedDate = item.created_at
    ? new Date(item.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    : 'Unknown date';

  if (item.status === 'failed') {
    return (
      <div className="bg-[#18181B] border border-red-500/30 rounded-2xl p-5">
        <div className="flex items-start gap-3">
          <span className="text-red-400 text-2xl flex-shrink-0">⚠️</span>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold text-red-400 mb-2">
              Generation Failed
            </div>
            <p className="text-xs text-[#8B949E] mb-1 truncate">{item.input_content}</p>
            <div className="text-xs text-[#8B949E] mb-3">
              {item.error_message ? getFriendlyErrorMessage(item.error_message) : 'Something went wrong. Please try again.'}
            </div>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1 text-green-400">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Credit refunded
              </div>
              <span className="text-gray-600">·</span>
              <span className="text-[#52525B]">{formattedDate}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-2xl overflow-hidden transition-all">
      {/* Card header */}
      <div className="flex items-center gap-4 p-5 hover:bg-[#27272A]/30 transition-colors">
        <div className={`flex-shrink-0 px-2 py-0.5 rounded text-[10px] font-black uppercase ${
          item.input_type === 'url' ? 'bg-[#3B82F6]/20 text-[#3B82F6]' 
          : item.input_type === 'video' ? 'bg-purple-500/20 text-purple-400'
          : 'bg-purple-500/20 text-purple-400'
        }`}>
          {item.input_type === 'video' ? '\uD83C\uDFAC Video' : item.input_type}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium text-sm truncate">
            {item.input_type === 'video'
              ? (item.seo_title || item.title || (item.input_content?.startsWith('preview:') ? 'Video Generation' : item.input_content) || 'Video Generation')
              : item.input_content
            }
          </p>
          {preview && <p className="text-[#52525B] text-xs mt-0.5 truncate italic">{preview}</p>}
          <p className="text-[#71717A] text-xs mt-0.5">{formattedDate}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {platforms.map(p => (
            <span key={p} className="text-[10px] font-semibold bg-[#27272A] text-[#A1A1AA] px-2 py-0.5 rounded-full">{p}</span>
          ))}
          {item.has_edits && (
            <span className="text-[10px] font-semibold text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded-full">✏ Edited</span>
          )}
        </div>
        {preview && (
          <button
            onClick={handleQuickCopy}
            className={`flex items-center justify-center gap-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors flex-shrink-0 ${quickCopied ? 'bg-green-500/20 text-green-400' : 'bg-[#27272A] text-[#A1A1AA] hover:text-white hover:bg-[#3F3F46]'}`}
            title="Quick copy first platform output"
          >
            {quickCopied ? '✓ Copied' : 'Copy'}
          </button>
        )}
        <button
          onClick={(e) => { e.stopPropagation(); onSchedule(item.id); }}
          className="flex items-center justify-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors shadow-lg shadow-blue-500/20 flex-shrink-0"
          title="Schedule content"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Schedule
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-xs font-medium text-white transition-colors flex-shrink-0"
        >
          {expanded ? 'Hide' : 'View'}
        </button>
      </div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full hidden"
      />

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-[#27272A] p-5 space-y-5">
          <PlatformSection label="Twitter / X" output={item.twitter_output} editedOutput={item.twitter_content_edited} />
          <PlatformSection label="LinkedIn" output={item.linkedin_output} editedOutput={item.linkedin_content_edited} />
          <PlatformSection label="TikTok" output={item.tiktok_output} editedOutput={item.tiktok_content_edited} />
          {(item.reels_title || item.reels_description) && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <p className="text-xs font-bold text-[#71717A] uppercase tracking-wider">Instagram Reels</p>
                {(item.reels_title_edited || item.reels_description_edited || item.reels_hashtags_edited) && (
                  <span className="text-[10px] font-semibold text-purple-400 bg-purple-500/10 border border-purple-500/20 px-1.5 py-0.5 rounded">edited</span>
                )}
              </div>
              {(item.reels_title_edited || item.reels_title) && (
                <div className="bg-[#09090B] rounded-xl p-4">
                  <p className="text-[10px] font-bold text-pink-400 uppercase tracking-widest mb-1">Title</p>
                  <p className="text-[#E4E4E7] text-sm leading-relaxed whitespace-pre-wrap">{item.reels_title_edited || item.reels_title}</p>
                </div>
              )}
              {(item.reels_description_edited || item.reels_description) && (
                <div className="bg-[#09090B] rounded-xl p-4">
                  <p className="text-[10px] font-bold text-pink-400 uppercase tracking-widest mb-1">Description</p>
                  <p className="text-[#E4E4E7] text-sm leading-relaxed whitespace-pre-wrap">{item.reels_description_edited || item.reels_description}</p>
                </div>
              )}
              {(item.reels_hashtags_edited || item.reels_hashtags) && (
                <div className="bg-[#09090B] rounded-xl p-4">
                  <p className="text-[10px] font-bold text-pink-400 uppercase tracking-widest mb-1">Hashtags</p>
                  <p className="text-[#E4E4E7] text-sm leading-relaxed whitespace-pre-wrap">{item.reels_hashtags_edited || item.reels_hashtags}</p>
                </div>
              )}
            </div>
          )}
          {(item.shorts_title || item.shorts_description) && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <p className="text-xs font-bold text-[#71717A] uppercase tracking-wider">YouTube Shorts</p>
                {(item.shorts_title_edited || item.shorts_description_edited || item.shorts_tags_edited) && (
                  <span className="text-[10px] font-semibold text-purple-400 bg-purple-500/10 border border-purple-500/20 px-1.5 py-0.5 rounded">edited</span>
                )}
              </div>
              {(item.shorts_title_edited || item.shorts_title) && (
                <div className="bg-[#09090B] rounded-xl p-4">
                  <p className="text-[10px] font-bold text-red-400 uppercase tracking-widest mb-1">Title</p>
                  <p className="text-[#E4E4E7] text-sm leading-relaxed whitespace-pre-wrap">{item.shorts_title_edited || item.shorts_title}</p>
                </div>
              )}
              {(item.shorts_description_edited || item.shorts_description) && (
                <div className="bg-[#09090B] rounded-xl p-4">
                  <p className="text-[10px] font-bold text-red-400 uppercase tracking-widest mb-1">Description</p>
                  <p className="text-[#E4E4E7] text-sm leading-relaxed whitespace-pre-wrap">{item.shorts_description_edited || item.shorts_description}</p>
                </div>
              )}
              {(item.shorts_tags_edited || item.shorts_tags) && (
                <div className="bg-[#09090B] rounded-xl p-4">
                  <p className="text-[10px] font-bold text-red-400 uppercase tracking-widest mb-1">Tags</p>
                  <p className="text-[#E4E4E7] text-sm leading-relaxed whitespace-pre-wrap">{item.shorts_tags_edited || item.shorts_tags}</p>
                </div>
              )}
            </div>
          )}
          
        </div>
      )}
    </div>
  );
}

export default function History() {
  const AUTO_POST_ENABLED_PLATFORMS = ['linkedin'];
  const { accounts: connectedAccounts, isConnected } = useConnectedAccounts();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [historyFilter, setHistoryFilter] = useState('all');
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [autoPostModalOpen, setAutoPostModalOpen] = useState(false);
  const [selectedGenerationId, setSelectedGenerationId] = useState(null);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('09:00');
  const [enableAutoPost, setEnableAutoPost] = useState(false);
  const [selectedAutoPostPlatforms, setSelectedAutoPostPlatforms] = useState([]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await api.getHistory();
        setHistory(data);
      } catch (e) {
        console.error('History fetch failed', e);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const getFriendlyErrorMessage = (technicalError) => {
    if (!technicalError) return "Something went wrong. Please try again.";
    
    const errorLower = technicalError.toLowerCase();
    
    // YouTube errors
    if (errorLower.includes('transcript') || errorLower.includes('youtube')) {
      return "Couldn't access this video's transcript. Try pasting the video content as raw text instead, or try a different video.";
    }
    
    // URL access errors
    if (errorLower.includes('403') || errorLower.includes('forbidden')) {
      return "This website blocked our access. Try pasting the article text directly instead.";
    }
    
    if (errorLower.includes('404') || errorLower.includes('not found')) {
      return "This page doesn't exist or has been removed. Please check the URL and try again.";
    }
    
    // API errors
    if (errorLower.includes('api') || errorLower.includes('rate limit')) {
      return "We're experiencing high demand. Please try again in a moment.";
    }
    
    // Default
    return "We couldn't generate content from this source. Try a different URL or paste the text directly.";
  };

  const openScheduleModal = (genId) => {
    setSelectedGenerationId(genId);
    setScheduleDate(new Date().toISOString().split('T')[0]);
    setScheduleTime('09:00');
    setEnableAutoPost(false);
    // Pre-select connected platforms for auto-posting
    const connectedPlatforms = connectedAccounts
      .map(acc => acc.platform)
      .filter(platform => AUTO_POST_ENABLED_PLATFORMS.includes(platform));
    setSelectedAutoPostPlatforms(connectedPlatforms);
    setScheduleModalOpen(true);
  };

  const openAutoPostModal = (genId) => {
    setSelectedGenerationId(genId);
    setAutoPostModalOpen(true);
  };

  const schedulePost = async () => {
    const allowedSelectedPlatforms = selectedAutoPostPlatforms.filter(platform =>
      AUTO_POST_ENABLED_PLATFORMS.includes(platform)
    );

    if (enableAutoPost && allowedSelectedPlatforms.length === 0) {
      showToast('❌ Select at least one available platform for auto-posting', 'error');
      return;
    }

    try {
      await api.request(`/generations/${selectedGenerationId}/schedule`, {
        method: 'PUT',
        body: JSON.stringify({
          scheduled_date: scheduleDate,
          scheduled_time: scheduleTime,
          platforms: enableAutoPost ? allowedSelectedPlatforms : ['all'],
          auto_post_enabled: enableAutoPost
        })
      });
      showToast(enableAutoPost ? '✅ Post scheduled with auto-posting!' : '✅ Post scheduled successfully!');
      setScheduleModalOpen(false);
    } catch (error) {
      console.error('Failed to schedule:', error);
      showToast('❌ Failed to schedule', 'error');
    }
  };

  const showToast = (message, type = 'success') => {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed; top: 24px; right: 24px; z-index: 9999;
      background: ${type === 'error' ? '#EF4444' : '#10B981'};
      color: white; padding: 16px 24px; border-radius: 12px;
      font-size: 15px; font-weight: 600; box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <svg className="animate-spin h-8 w-8 text-[#3B82F6]" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-4 md:p-8 text-center">
        <div className="w-16 h-16 rounded-2xl bg-[#27272A] flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-[#71717A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-white font-bold text-xl mb-2">No generations yet</h3>
        <p className="text-[#71717A]">Your generated threads will appear here.</p>
      </div>
    );
  }

  const successfulItems = history.filter(i => i.status !== 'failed');
  const failedItems = history.filter(i => i.status === 'failed');
  
  // Filter generations based on selected tab
  const filteredGenerations = history.filter(gen => {
    if (historyFilter === 'success') return gen.status !== 'failed';
    if (historyFilter === 'failed') return gen.status === 'failed';
    return true; // 'all'
  });
  const autoPostEligibleAccounts = connectedAccounts.filter(acc =>
    AUTO_POST_ENABLED_PLATFORMS.includes(acc.platform)
  );
  const hasPausedConnectedAccounts = connectedAccounts.some(acc =>
    !AUTO_POST_ENABLED_PLATFORMS.includes(acc.platform)
  );

  return (
    <div className="max-w-4xl mx-auto px-4 py-4 md:p-8 space-y-4 md:space-y-6">
      <header>
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-1">History</h2>
        <p className="text-[#A1A1AA]">
          {history.length} generation{history.length !== 1 ? 's' : ''} total
        </p>
      </header>
      
      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-gray-800">
        <button
          onClick={() => setHistoryFilter('all')}
          className={`
            px-4 py-2 text-sm font-medium transition-colors border-b-2
            ${historyFilter === 'all'
              ? 'text-blue-400 border-blue-400'
              : 'text-gray-400 border-transparent hover:text-gray-300'
            }
          `}
        >
          All ({history.length})
        </button>
        
        <button
          onClick={() => setHistoryFilter('success')}
          className={`
            px-4 py-2 text-sm font-medium transition-colors border-b-2
            ${historyFilter === 'success'
              ? 'text-green-400 border-green-400'
              : 'text-gray-400 border-transparent hover:text-gray-300'
            }
          `}
        >
          <span className="mr-1">✓</span>
          Success ({successfulItems.length})
        </button>
        
        <button
          onClick={() => setHistoryFilter('failed')}
          className={`
            px-4 py-2 text-sm font-medium transition-colors border-b-2
            ${historyFilter === 'failed'
              ? 'text-red-400 border-red-400'
              : 'text-gray-400 border-transparent hover:text-gray-300'
            }
          `}
        >
          <span className="mr-1">✗</span>
          Failed ({failedItems.length})
        </button>
      </div>
      
      <div className="space-y-3">
        {filteredGenerations.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-600 mb-2">
              {historyFilter === 'all' ? 'No generations yet' :
               historyFilter === 'success' ? 'No successful generations yet' :
               'No failed generations'}
            </div>
          </div>
        ) : (
          filteredGenerations.map((item) => (
            <HistoryCard key={item.id} item={item} onSchedule={openScheduleModal} onAutoPost={openAutoPostModal} getFriendlyErrorMessage={getFriendlyErrorMessage} />
          ))
        )}
      </div>

      {/* Schedule Modal */}
      {scheduleModalOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#18181B] border border-[#27272A] rounded-xl p-6 max-w-md w-full mx-4 space-y-4">
            <h3 className="text-xl font-bold text-white">Schedule Post</h3>
            
            <div>
              <label className="block text-xs font-bold text-[#71717A] uppercase tracking-wider mb-2">Date</label>
              <input
                type="date"
                value={scheduleDate}
                onChange={(e) => setScheduleDate(e.target.value)}
                className="w-full px-3 py-2 bg-[#09090B] border border-[#27272A] rounded-lg text-white focus:border-[#3B82F6] outline-none"
              />
            </div>
            
            <div>
              <label className="block text-xs font-bold text-[#71717A] uppercase tracking-wider mb-2">Time</label>
              <input
                type="time"
                value={scheduleTime}
                onChange={(e) => setScheduleTime(e.target.value)}
                className="w-full px-3 py-2 bg-[#09090B] border border-[#27272A] rounded-lg text-white focus:border-[#3B82F6] outline-none"
              />
            </div>
            
            {/* Auto-Posting Toggle */}
            <div className="p-4 bg-[#09090B] border border-[#27272A] rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-white">⚡ Auto-Posting</div>
                  <div className="text-xs text-[#71717A] mt-0.5">
                    Publish automatically at scheduled time
                  </div>
                </div>
                <button
                  onClick={() => {
                    setEnableAutoPost(!enableAutoPost);
                    // Auto-select connected platforms when enabling
                    if (!enableAutoPost) {
                      const connectedPlatforms = connectedAccounts
                        .map(acc => acc.platform)
                        .filter(platform => AUTO_POST_ENABLED_PLATFORMS.includes(platform));
                      setSelectedAutoPostPlatforms(connectedPlatforms);
                    }
                  }}
                  className={`
                    relative w-12 h-6 rounded-full transition-colors flex-shrink-0
                    ${enableAutoPost ? 'bg-[#3B82F6]' : 'bg-[#27272A]'}
                  `}
                >
                  <div className={`
                    absolute top-1 w-4 h-4 bg-white rounded-full transition-transform
                    ${enableAutoPost ? 'translate-x-7' : 'translate-x-1'}
                  `} />
                </button>
              </div>
              
              {enableAutoPost && (
                <div className="pt-3 border-t border-[#27272A] space-y-2">
                  <div className="text-xs font-bold text-[#71717A] uppercase tracking-wider">Post to:</div>
                  <div className="text-xs text-[#93C5FD] bg-[#3B82F6]/10 border border-[#3B82F6]/20 p-2 rounded">
                    LinkedIn-only mode is enabled right now.
                  </div>
                  {autoPostEligibleAccounts.length > 0 ? (
                    <div className="space-y-2">
                      {autoPostEligibleAccounts.map(account => (
                        <label key={account.platform} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedAutoPostPlatforms.includes(account.platform)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedAutoPostPlatforms([...selectedAutoPostPlatforms, account.platform]);
                              } else {
                                setSelectedAutoPostPlatforms(selectedAutoPostPlatforms.filter(p => p !== account.platform));
                              }
                            }}
                            className="w-4 h-4 rounded border-[#3B82F6] bg-[#09090B] cursor-pointer"
                          />
                          <span className="text-sm text-[#A1A1AA] capitalize">{account.platform}</span>
                          <span className="text-xs text-[#52525B]">(@{account.username})</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-yellow-600 bg-yellow-500/10 border border-yellow-500/20 p-2 rounded">
                      No LinkedIn account connected. Go to Settings to connect LinkedIn for auto-posting.
                    </div>
                  )}
                  {hasPausedConnectedAccounts && (
                    <div className="text-xs text-[#71717A]">
                      Twitter/X and Instagram are connected but paused for auto-posting.
                    </div>
                  )}
                </div>
              )}
              
              {!enableAutoPost && (
                <div className="pt-3 border-t border-[#27272A] text-xs text-[#52525B]">
                  💌 You'll get an email reminder to post manually
                </div>
              )}
            </div>
            
            <div className="flex gap-3 pt-4">
              <button
                onClick={() => setScheduleModalOpen(false)}
                className="flex-1 px-4 py-2 bg-[#27272A] hover:bg-[#3F3F46] text-white text-sm font-medium rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={schedulePost}
                disabled={enableAutoPost && selectedAutoPostPlatforms.length === 0}
                className="flex-1 px-4 py-2 bg-[#3B82F6] hover:bg-[#2563EB] disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
              >
                {enableAutoPost ? '⚡ Schedule & Auto-Post' : '📅 Schedule'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Auto-Post Scheduler Modal */}
      {autoPostModalOpen && (
        <AutoPostScheduler
          generationId={selectedGenerationId}
          onClose={() => setAutoPostModalOpen(false)}
          onScheduled={() => {
            setAutoPostModalOpen(false);
            // Could refresh history or show success message
          }}
        />
      )}
    </div>
  );
}
