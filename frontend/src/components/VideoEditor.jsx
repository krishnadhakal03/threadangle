import React, { useState, useRef } from 'react';
import { SketchPicker } from 'react-color';
import { api } from '../utils/api';

const BASE = import.meta.env.VITE_API_URL || '';

const TABS = [
  { key: 'thumbnail', icon: '🖼', label: 'Thumbnail' },
  { key: 'seo', icon: '🔍', label: 'SEO' },
  { key: 'platform', icon: '📱', label: 'Platforms' },
  { key: 'captions', icon: '🎬', label: 'Captions' },
];

const PLATFORMS = [
  { key: 'youtube_shorts', icon: '▶', label: 'YouTube Shorts', titleLimit: 100, descLimit: 5000 },
  { key: 'reels', icon: '📸', label: 'Reels', titleLimit: 60, descLimit: 2200 },
  { key: 'tiktok', icon: '🎵', label: 'TikTok', titleLimit: 150, descLimit: 2200 },
];

function CharCount({ value, max }) {
  const len = (value || '').length;
  const pct = max ? len / max : 0;
  const color = pct > 1 ? 'text-red-400' : pct > 0.85 ? 'text-amber-400' : 'text-[#484F58]';
  return <span className={`text-[10px] font-mono ${color}`}>{len}{max ? `/${max}` : ''}</span>;
}

const inputCls =
  'w-full bg-[#0D1117] border border-[#30363D] rounded-lg px-3 py-2.5 text-[#E6EDF3] text-sm placeholder:text-[#484F58] focus:border-[#388bfd] focus:ring-1 focus:ring-[#388bfd]/30 outline-none transition';
const textareaCls = inputCls + ' resize-none';
const labelCls = 'block text-[11px] font-semibold text-[#8B949E] uppercase tracking-widest mb-1.5';

function resolveThumbnail(url) {
  if (!url) return '';
  if (url.startsWith('http') || url.startsWith('blob:') || url.startsWith('data:')) return url;
  return `${BASE}${url.startsWith('/') ? '' : '/api/generate'}${url}`;
}

export default function VideoEditor({ video, onSave }) {
  const [activeTab, setActiveTab] = useState('thumbnail');
  const [platformTab, setPlatformTab] = useState('youtube_shorts');

  const [thumbnail, setThumbnail] = useState(video?.thumbnail_url || '');
  const [previousThumbnail, setPreviousThumbnail] = useState('');
  const [thumbnailText, setThumbnailText] = useState(video?.seo?.thumbnail_text || video?.seo_title || '');
  const [thumbnailRefreshing, setThumbnailRefreshing] = useState(false);
  const [thumbnailError, setThumbnailError] = useState(false);

  const [seo, setSeo] = useState({
    title: video?.seo?.title || video?.seo_title || '',
    description: video?.seo?.description || '',
    tags: Array.isArray(video?.seo?.tags) ? video.seo.tags.join(', ') : '',
    hashtags: Array.isArray(video?.seo?.hashtags) ? video.seo.hashtags.join(' ') : '',
  });

  const [platformMeta, setPlatformMeta] = useState(video?.platform_meta || {});

  const [captions, setCaptions] = useState(video?.captions || []);
  const [selectedCaption, setSelectedCaption] = useState(null);
  const [captionStyle, setCaptionStyle] = useState({
    color: '#FFFFFF',
    fontSize: 72,
    fontFamily: 'Impact',
    strokeColor: '#000000',
    strokeWidth: 4,
    ...(video?.editor?.caption_style || {}),
  });
  const [showColorPicker, setShowColorPicker] = useState(false);

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  const videoRef = useRef(null);

  const markDirty = () => setIsDirty(true);

  const updateCaptionText = (index, newText) => {
    const updated = [...captions];
    updated[index] = { ...updated[index], text: newText };
    setCaptions(updated);
    markDirty();
  };

  const updateThumbnail = async () => {
    setThumbnailRefreshing(true);
    setThumbnailError(false);
    try {
      const data = await api.regenerateThumbnail({ video_id: video.id, thumbnail_text: thumbnailText });
      if (data.thumbnail_url) {
        const bust = `${data.thumbnail_url}${data.thumbnail_url.includes('?') ? '&' : '?'}t=${Date.now()}`;
        setPreviousThumbnail(thumbnail || '');
        setThumbnail(bust);
        setThumbnailError(false);
        markDirty();
      }
    } catch {
      setThumbnailError(true);
    } finally {
      setThumbnailRefreshing(false);
    }
  };

  const activePlatformMeta = platformMeta?.[platformTab] || { title: '', description: '', hashtags: '' };
  const activePlatform = PLATFORMS.find((p) => p.key === platformTab) || PLATFORMS[0];

  const updatePlatformMeta = (field, value) => {
    setPlatformMeta((prev) => ({
      ...prev,
      [platformTab]: { ...(prev?.[platformTab] || {}), [field]: value },
    }));
    markDirty();
  };

  const platformFilled = PLATFORMS.filter((p) => {
    const m = platformMeta?.[p.key];
    return m?.title || m?.description;
  }).length;

  const saveChanges = async () => {
    setSaving(true);
    setSaveError('');
    setSaveSuccess(false);
    try {
      await onSave({
        video_id: video.id,
        captions,
        caption_style: captionStyle,
        thumbnail_text: thumbnailText,
        seo: { ...seo, tags: seo.tags, hashtags: seo.hashtags },
        platform_meta: platformMeta,
      });
      setIsDirty(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setSaveError(err?.message || 'Save failed. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col" style={{ minHeight: '560px', maxHeight: '82vh' }}>
      <div className="flex flex-col lg:flex-row flex-1 min-h-0 overflow-hidden">

        {/* LEFT: video + quick stats */}
        <div className="lg:w-[300px] xl:w-[320px] flex-shrink-0 bg-[#010409] border-r border-[#21262D] flex flex-col">
          <div
            className="relative bg-black flex items-center justify-center overflow-hidden flex-shrink-0"
            style={{ aspectRatio: '9/16', maxHeight: '320px' }}
          >
            {video?.video_url ? (
              <video
                ref={videoRef}
                src={video.video_url}
                controls
                className="h-full w-auto object-contain"
                style={{ maxHeight: '320px' }}
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-[#484F58] gap-2 p-8">
                <div className="text-4xl">🎬</div>
                <p className="text-xs text-center">No video available yet</p>
              </div>
            )}
            {video?.status && (
              <div className="absolute top-2 right-2">
                <span className={`text-[10px] font-semibold px-2 py-1 rounded-full ${
                  video.status === 'success'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                }`}>
                  {video.status}
                </span>
              </div>
            )}
          </div>

          <div className="p-4 space-y-2 overflow-y-auto flex-1">
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-[#161B22] border border-[#21262D] rounded-lg p-3">
                <div className="text-[10px] uppercase font-bold tracking-widest text-[#484F58]">SEO Title</div>
                <div className="text-xs text-[#C9D1D9] mt-1.5 leading-snug line-clamp-2">
                  {seo.title || <span className="text-[#484F58]">None</span>}
                </div>
              </div>
              <div className="bg-[#161B22] border border-[#21262D] rounded-lg p-3">
                <div className="text-[10px] uppercase font-bold tracking-widest text-[#484F58]">Platforms</div>
                <div className="text-xs text-[#C9D1D9] mt-1.5">{platformFilled}/{PLATFORMS.length} filled</div>
              </div>
            </div>
            <div className="bg-[#161B22] border border-[#21262D] rounded-lg p-3">
              <div className="text-[10px] uppercase font-bold tracking-widest text-[#484F58]">Thumbnail Text</div>
              <div className="text-xs text-[#C9D1D9] mt-1.5">
                {thumbnailText || <span className="text-[#484F58]">None</span>}
              </div>
            </div>
            {captions.length > 0 && (
              <div className="bg-[#161B22] border border-[#21262D] rounded-lg p-3">
                <div className="text-[10px] uppercase font-bold tracking-widest text-[#484F58]">Captions</div>
                <div className="text-xs text-[#C9D1D9] mt-1.5">
                  {captions.length} line{captions.length !== 1 ? 's' : ''}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: editor */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#0D1117]">
          <div className="border-b border-[#21262D] px-5 pt-4 flex-shrink-0">
            <div className="flex gap-1 overflow-x-auto">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-semibold rounded-t-lg border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.key
                      ? 'border-[#388bfd] text-white bg-[#388bfd]/10'
                      : 'border-transparent text-[#8B949E] hover:text-[#C9D1D9] hover:bg-[#161B22]'
                  }`}
                >
                  <span className="text-base leading-none">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-1">

            {/* THUMBNAIL */}
            {activeTab === 'thumbnail' && (
              <div className="space-y-5 max-w-xl">
                <div>
                  <h2 className="text-white font-bold text-base">Thumbnail</h2>
                  <p className="text-[#8B949E] text-xs mt-1">Shown as the cover image on all platforms. Keep text under 6 words.</p>
                </div>

                {previousThumbnail ? (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <div className="text-[10px] uppercase font-bold tracking-widest text-[#484F58]">Before</div>
                      <div className="rounded-xl overflow-hidden border border-[#30363D] bg-black">
                        <img src={resolveThumbnail(previousThumbnail)} alt="Previous" className="w-full object-cover" />
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <div className="text-[10px] uppercase font-bold tracking-widest text-[#388bfd]">Current</div>
                      <div className="rounded-xl overflow-hidden border border-[#388bfd]/40 bg-black">
                        {thumbnail ? (
                          <img src={resolveThumbnail(thumbnail)} alt="Current" className="w-full object-cover" onError={() => setThumbnailError(true)} />
                        ) : (
                          <div className="aspect-video flex items-center justify-center text-[#484F58] text-xs">No thumbnail</div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl overflow-hidden border border-[#30363D] bg-black" style={{ maxWidth: '220px' }}>
                    {thumbnail && !thumbnailError ? (
                      <img src={resolveThumbnail(thumbnail)} alt="Thumbnail" className="w-full object-cover" onError={() => setThumbnailError(true)} />
                    ) : (
                      <div className="aspect-video flex flex-col items-center justify-center text-[#484F58] gap-2">
                        <div className="text-2xl">🖼</div>
                        <div className="text-xs">No thumbnail yet</div>
                      </div>
                    )}
                  </div>
                )}

                {thumbnailError && (
                  <div className="flex items-start gap-3 bg-[#161B22] border border-[#30363D] rounded-xl px-4 py-3">
                    <span className="text-lg mt-0.5 flex-shrink-0">🖼</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-[#C9D1D9] mb-0.5">No thumbnail yet</p>
                      <p className="text-xs text-[#484F58] leading-relaxed">Enter overlay text below and click <span className="text-[#388bfd]">Regenerate Thumbnail</span> to create one from the video.</p>
                    </div>
                  </div>
                )}

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className={labelCls}>Thumbnail Text</label>
                    <CharCount value={thumbnailText} max={40} />
                  </div>
                  <input
                    type="text"
                    maxLength={60}
                    value={thumbnailText}
                    onChange={(e) => { setThumbnailText(e.target.value); markDirty(); }}
                    placeholder="e.g. WASTE $1,000? Here's why…"
                    className={inputCls}
                  />
                  <p className="text-[11px] text-[#484F58] mt-1.5">Short punchy headline rendered as overlay text on the thumbnail.</p>
                </div>

                <button
                  onClick={updateThumbnail}
                  disabled={thumbnailRefreshing}
                  className="flex items-center gap-2 px-4 py-2.5 bg-[#1F6FEB] hover:bg-[#388bfd] disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white text-sm font-semibold transition-colors"
                >
                  {thumbnailRefreshing ? (
                    <>
                      <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Regenerating…
                    </>
                  ) : <>↺ Regenerate Thumbnail</>}
                </button>
              </div>
            )}

            {/* SEO */}
            {activeTab === 'seo' && (
              <div className="space-y-5 max-w-xl">
                <div>
                  <h2 className="text-white font-bold text-base">SEO Metadata</h2>
                  <p className="text-[#8B949E] text-xs mt-1">Used when uploading via platform APIs. Optimise for click-through rate and search rank.</p>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className={labelCls}>Title</label>
                    <CharCount value={seo.title} max={60} />
                  </div>
                  <input
                    value={seo.title}
                    onChange={(e) => { setSeo((p) => ({ ...p, title: e.target.value })); markDirty(); }}
                    placeholder="Attention-grabbing video title…"
                    className={inputCls}
                  />
                  <p className="text-[11px] text-[#484F58] mt-1">Google Search shows ~60 characters.</p>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className={labelCls}>Description</label>
                    <CharCount value={seo.description} max={160} />
                  </div>
                  <textarea rows={4} value={seo.description}
                    onChange={(e) => { setSeo((p) => ({ ...p, description: e.target.value })); markDirty(); }}
                    placeholder="Describe the video for search engines and viewers…"
                    className={textareaCls}
                  />
                  <p className="text-[11px] text-[#484F58] mt-1">Meta description snippet (~160 chars).</p>
                </div>
                <div>
                  <label className={labelCls}>Tags <span className="normal-case font-normal text-[#484F58]">(comma-separated)</span></label>
                  <input value={seo.tags}
                    onChange={(e) => { setSeo((p) => ({ ...p, tags: e.target.value })); markDirty(); }}
                    placeholder="finance, investing, money tips"
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className={labelCls}>Hashtags</label>
                  <textarea rows={2} value={seo.hashtags}
                    onChange={(e) => { setSeo((p) => ({ ...p, hashtags: e.target.value })); markDirty(); }}
                    placeholder="#finance #investing #moneytips"
                    className={textareaCls}
                  />
                </div>
              </div>
            )}

            {/* PLATFORM META */}
            {activeTab === 'platform' && (
              <div className="space-y-5 max-w-xl">
                <div>
                  <h2 className="text-white font-bold text-base">Platform Metadata</h2>
                  <p className="text-[#8B949E] text-xs mt-1">Tailor captions and titles per platform to maximise reach on each channel.</p>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {PLATFORMS.map((p) => {
                    const filled = !!(platformMeta?.[p.key]?.title || platformMeta?.[p.key]?.description);
                    return (
                      <button key={p.key} onClick={() => setPlatformTab(p.key)}
                        className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors ${
                          platformTab === p.key
                            ? 'bg-[#1F6FEB] text-white'
                            : 'bg-[#161B22] border border-[#30363D] text-[#8B949E] hover:text-white hover:border-[#484F58]'
                        }`}
                      >
                        <span>{p.icon}</span>{p.label}
                        {filled && platformTab !== p.key && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0" />}
                      </button>
                    );
                  })}
                </div>
                <p className="text-[11px] text-[#484F58]">Title limit: {activePlatform.titleLimit} chars · Description: {activePlatform.descLimit.toLocaleString()} chars</p>
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className={labelCls}>Title</label>
                    <CharCount value={activePlatformMeta.title} max={activePlatform.titleLimit} />
                  </div>
                  <input value={activePlatformMeta.title || ''}
                    onChange={(e) => updatePlatformMeta('title', e.target.value)}
                    placeholder={`${activePlatform.label} title…`}
                    className={inputCls}
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className={labelCls}>Description / Caption</label>
                    <CharCount value={activePlatformMeta.description} max={activePlatform.descLimit} />
                  </div>
                  <textarea rows={5} value={activePlatformMeta.description || ''}
                    onChange={(e) => updatePlatformMeta('description', e.target.value)}
                    placeholder="Caption or description shown under the video…"
                    className={textareaCls}
                  />
                </div>
                <div>
                  <label className={labelCls}>Hashtags</label>
                  <textarea rows={2} value={activePlatformMeta.hashtags || ''}
                    onChange={(e) => updatePlatformMeta('hashtags', e.target.value)}
                    placeholder="#yourhashtags #here"
                    className={textareaCls}
                  />
                </div>
              </div>
            )}

            {/* CAPTIONS */}
            {activeTab === 'captions' && (
              <div className="space-y-5 max-w-xl">
                <div>
                  <h2 className="text-white font-bold text-base">Captions & Style</h2>
                  <p className="text-[#8B949E] text-xs mt-1">Edit caption text inline and control how subtitles are rendered on the exported video.</p>
                </div>

                {captions.length > 0 ? (
                  <div className="space-y-2">
                    {captions.map((caption, index) => (
                      <div key={index} className={`rounded-xl border transition-colors ${
                        selectedCaption === index
                          ? 'border-[#388bfd] bg-[#388bfd]/5'
                          : 'border-[#21262D] bg-[#161B22] hover:border-[#30363D]'
                      }`}>
                        <div onClick={() => setSelectedCaption(selectedCaption === index ? null : index)}
                          className="flex items-center justify-between px-4 py-3 cursor-pointer">
                          <span className="text-xs font-mono text-[#8B949E]">{caption.start_time}s → {caption.end_time}s</span>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={(e) => { e.stopPropagation(); if (videoRef.current) videoRef.current.currentTime = caption.start_time; }}
                              className="text-xs text-[#388bfd] hover:text-white px-2 py-0.5 rounded border border-[#388bfd]/30 hover:bg-[#388bfd]/10 transition-colors"
                            >Jump ↗</button>
                            <span className="text-[10px] text-[#484F58]">{selectedCaption === index ? '▲' : '▼'}</span>
                          </div>
                        </div>
                        {selectedCaption === index ? (
                          <div className="px-4 pb-3">
                            <input type="text" autoFocus value={caption.text}
                              onChange={(e) => updateCaptionText(index, e.target.value)}
                              className={inputCls}
                            />
                          </div>
                        ) : (
                          <div className="px-4 pb-3 text-sm text-[#C9D1D9] line-clamp-1">{caption.text}</div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-[#21262D] bg-[#161B22] py-10 text-center">
                    <div className="text-2xl mb-2">🎬</div>
                    <p className="text-sm text-[#8B949E]">No captions available</p>
                    <p className="text-xs text-[#484F58] mt-1">Captions are generated automatically with the video</p>
                  </div>
                )}

                <div className="border border-[#21262D] rounded-xl bg-[#161B22] p-5 space-y-5">
                  <div className="text-sm font-semibold text-[#C9D1D9]">Caption Style</div>
                  <div>
                    <label className={labelCls}>Text Color</label>
                    <div className="flex items-center gap-3">
                      <button onClick={() => setShowColorPicker(!showColorPicker)}
                        className="w-10 h-10 rounded-lg border-2 border-[#30363D] cursor-pointer flex-shrink-0"
                        style={{ backgroundColor: captionStyle.color }}
                      />
                      <span className="text-sm font-mono text-[#8B949E]">{captionStyle.color}</span>
                    </div>
                    {showColorPicker && (
                      <>
                        <div className="fixed inset-0 z-10" onClick={() => setShowColorPicker(false)} />
                        <div className="relative z-20 mt-2 w-fit">
                          <SketchPicker color={captionStyle.color}
                            onChange={(c) => { setCaptionStyle((p) => ({ ...p, color: c.hex })); markDirty(); }}
                          />
                        </div>
                      </>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className={labelCls}>Font Size</label>
                      <span className="text-xs font-mono text-[#8B949E]">{captionStyle.fontSize}px</span>
                    </div>
                    <input type="range" min="36" max="96" value={captionStyle.fontSize}
                      onChange={(e) => { setCaptionStyle((p) => ({ ...p, fontSize: +e.target.value })); markDirty(); }}
                      className="w-full accent-blue-500"
                    />
                    <div className="flex justify-between text-[10px] text-[#484F58] mt-1"><span>36px</span><span>96px</span></div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className={labelCls}>Stroke Width</label>
                      <span className="text-xs font-mono text-[#8B949E]">{captionStyle.strokeWidth}px</span>
                    </div>
                    <input type="range" min="0" max="8" value={captionStyle.strokeWidth}
                      onChange={(e) => { setCaptionStyle((p) => ({ ...p, strokeWidth: +e.target.value })); markDirty(); }}
                      className="w-full accent-blue-500"
                    />
                    <div className="flex justify-between text-[10px] text-[#484F58] mt-1"><span>None</span><span>Heavy</span></div>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      {/* sticky save bar */}
      <div className="border-t border-[#21262D] bg-[#0D1117] px-6 py-3 flex items-center justify-between gap-4 flex-shrink-0">
        <div>
          {isDirty ? (
            <span className="flex items-center gap-1.5 text-xs text-amber-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              Unsaved changes
            </span>
          ) : saveSuccess ? (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Saved successfully
            </span>
          ) : (
            <span className="text-xs text-[#484F58]">All changes saved</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {saveError && <span className="text-xs text-red-400">{saveError}</span>}
          <button onClick={saveChanges} disabled={saving}
            className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition-colors"
          >
            {saving ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Saving…
              </>
            ) : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
