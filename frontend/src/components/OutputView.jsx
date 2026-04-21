import React from 'react';
import SocialPlatformIcon from './SocialPlatformIcon';
import { useDialog } from '../context/DialogContext';

export default function OutputView({ data, onReset }) {
  const { alert: showAlert } = useDialog();

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      await showAlert({
        title: 'Copied',
        message: 'Copied to clipboard!',
        confirmText: 'Great',
        tone: 'success',
      });
    } catch {
      await showAlert({
        title: 'Copy Failed',
        message: 'Could not copy to clipboard. Please try again.',
        confirmText: 'OK',
        tone: 'danger',
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-12 duration-1000">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-black text-white mb-2 leading-none uppercase">Genius Content Ready</h2>
          <p className="text-gray-400 font-medium">Your platform-optimized posts have been crafted.</p>
        </div>
        <button 
          onClick={onReset}
          className="bg-dark border border-border hover:border-accent text-white font-bold py-2 px-6 rounded-xl transition-all text-sm uppercase tracking-widest"
        >
          ✨ New Generate
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {data.twitter && (
          <div className="bg-card border border-border rounded-2xl overflow-hidden glassmorphism flex flex-col">
            <div className="bg-accent/10 p-4 border-b border-border flex justify-between items-center">
              <span className="text-white font-black text-sm uppercase tracking-widest">Twitter (X) Thread</span>
              <span className="text-accent text-lg">𝕏</span>
            </div>
            <div className="p-6 space-y-4 flex-1">
              <div className="bg-dark/50 p-4 rounded-xl border border-border/50 relative group">
                <p className="text-sm text-gray-300 italic mb-2">Hook Tweet:</p>
                <p className="text-white font-medium">{data.twitter.hook}</p>
                <button 
                  onClick={() => copyToClipboard(data.twitter.hook)}
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-accent px-2 py-1 rounded text-[10px] font-bold"
                >
                  COPY
                </button>
              </div>
              <div className="space-y-3">
                {data.twitter.thread.map((tweet, i) => (
                  <div key={i} className="bg-dark/30 p-4 rounded-xl border border-border/30 text-sm text-gray-300">
                    <span className="text-accent font-bold mr-2">{i + 1}/</span>
                    {tweet}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {data.linkedin && (
          <div className="bg-card border border-border rounded-2xl overflow-hidden glassmorphism flex flex-col">
            <div className="bg-blue-500/10 p-4 border-b border-border flex justify-between items-center">
              <span className="text-white font-black text-sm uppercase tracking-widest">LinkedIn Post</span>
              <span className="text-blue-500"><SocialPlatformIcon platform="linkedin" className="w-5 h-5" /></span>
            </div>
            <div className="p-6 space-y-6 flex-1">
              <div className="space-y-2">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">Headline</p>
                <p className="text-xl font-bold text-white">{data.linkedin.title}</p>
              </div>
              <div className="space-y-2 flex-1">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">Body</p>
                <div className="bg-dark/50 p-6 rounded-xl border border-border/50 text-gray-300 text-sm h-full whitespace-pre-wrap leading-relaxed">
                  {data.linkedin.body}
                </div>
              </div>
              <button 
                onClick={() => copyToClipboard(`${data.linkedin.title}\n\n${data.linkedin.body}`)}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl transition-all shadow-xl shadow-blue-600/20 uppercase tracking-widest text-xs"
              >
                Copy Entire Post
              </button>
            </div>
          </div>
        )}

        {data.tiktok && (
          <div className="bg-card border border-border rounded-2xl overflow-hidden glassmorphism lg:col-span-2">
            <div className="bg-pink-500/10 p-4 border-b border-border flex justify-between items-center">
              <span className="text-white font-black text-sm uppercase tracking-widest">Viral Video Script (TikTok/Reels)</span>
              <span className="text-pink-500"><SocialPlatformIcon platform="tiktok" className="w-5 h-5" /></span>
            </div>
            <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-12">
              <div className="space-y-6">
                <div className="space-y-2">
                  <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">Hook Line</p>
                  <p className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-accent italic">"{data.tiktok.hook_line}"</p>
                </div>
                <div className="space-y-4">
                   <div className="bg-accent/5 p-4 rounded-xl border border-accent/20 mb-4">
                     <p className="text-[10px] font-bold text-accent uppercase tracking-widest mb-1">Audio Suggestion</p>
                     <p className="text-sm text-white font-medium italic">{data.tiktok.audio_suggestion}</p>
                   </div>
                   {Object.entries(data.tiktok.script).map(([key, val]) => (
                     <div key={key} className="flex gap-4 group">
                       <span className="w-24 text-[10px] font-bold text-gray-600 uppercase mt-1 shrink-0">{key}</span>
                       <p className="flex-1 text-sm text-white font-medium leading-relaxed bg-dark/20 p-3 rounded-lg border border-border/10 group-hover:border-border/30 transition-colors">{val}</p>
                     </div>
                   ))}
                </div>
              </div>
              <div className="space-y-6">
                <div className="bg-dark/50 p-6 rounded-2xl border-2 border-dashed border-border/50">
                  <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4 italic">On-Screen Text Overlays</p>
                  <div className="space-y-3">
                    {data.tiktok.on_screen_text.map((text, i) => (
                      <div key={i} className="bg-white text-black font-black px-4 py-2 rounded-lg text-center shadow-lg transform -rotate-1">
                        {text}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">Caption</p>
                  <p className="text-sm text-gray-400">{data.tiktok.caption}</p>
                   <div className="flex gap-2 flex-wrap mt-3">
                     {data.tiktok.hashtags.map(tag => (
                       <span key={tag} className="text-accent text-xs font-bold">#{tag}</span>
                     ))}
                   </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
