import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SocialPlatformIcon from '../components/SocialPlatformIcon';

const DemoPage = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activePlatform, setActivePlatform] = useState('twitter');
  const [voiceTab, setVoiceTab] = useState('after');

  const sampleURL = "https://example.com/blog/5-productivity-hacks-that-changed-my-life";
  
  const demoContent = {
    twitter: `1/ Most people think productivity is about doing more.

They're dead wrong.

Here's what actually works (learned this the hard way):

2/ Real productivity isn't cramming more into your day.

It's doing the RIGHT things and eliminating everything else.

Sounds obvious. Nobody does it.

3/ Hack #1: The 2-Hour Rule

Block 2 hours every morning. No meetings, no emails, no Slack.

Just your most important work.

This alone 3x'd my output in 30 days.

4/ Hack #2: The "Hell Yes or No" Filter

If something isn't a "HELL YES!" — it's a no.

Meetings, collaborations, side projects — everything.

Your calendar will thank you.

5/ Hack #3: Kill Your To-Do List

Replace it with a "Top 3" list.

What are the 3 things that MUST get done today?

Everything else is optional.

6/ Hack #4: Time Block Like Your Life Depends On It

Every hour planned. Zero room for "I'll figure it out later."

Sounds rigid. Changed everything.

7/ Hack #5: Weekly Reviews

Every Friday, review what worked and what didn't.

Double down on what works. Kill what doesn't.

This is how you actually improve instead of just staying busy.

8/ Bottom line:

Productivity isn't hustle culture. It's focus culture.

If you found this helpful, follow me for more no-BS productivity tips.

What's your #1 productivity hack? 👇`,

    linkedin: `Most people think productivity is about doing more.

They're wrong.

After burning out twice, I learned that real productivity isn't about cramming more into your day. It's about doing the RIGHT things and ruthlessly eliminating everything else.

Here are 5 productivity hacks that changed my life:

1. The 2-Hour Rule
Block 2 uninterrupted hours every morning. No meetings, no emails, no Slack. Just your most important work. This alone tripled my output in 30 days.

2. The "Hell Yes or No" Filter
If something isn't a "HELL YES!" — it's automatically a no. Apply this to meetings, collaborations, side projects — everything. Your calendar will thank you.

3. Kill Your To-Do List
Replace it with a "Top 3" list. What are the 3 things that MUST get done today? Everything else is optional. This turns overwhelm into clarity.

4. Time Block Like Your Life Depends On It
Plan every hour of your day. Zero room for "I'll figure it out later." It sounds rigid, but it's the reason I actually finish what I start.

5. Weekly Reviews
Every Friday, review what worked and what didn't. Double down on what works. Kill what doesn't. This is how you improve instead of just staying busy.

Real productivity isn't hustle culture. It's focus culture.

What's your #1 productivity rule?

#Productivity #TimeManagement #WorkSmart #Focus #Efficiency`,

    tiktok: `🎬 HOOK (0-3 seconds)
Everyone talks about "productivity hacks" but most of them are garbage.

📱 SETUP (3-10 seconds)
I tried every productivity tip on the internet for 2 years. Most made me LESS productive. But 5 things actually worked — and one of them tripled my output in 30 days.

💡 VALUE (10-45 seconds)
Here's what actually works:

Number 1: Block 2 hours every morning for deep work. No meetings, no emails. Just your most important task. This changed everything.

Number 2: Use the "Hell Yes or No" filter. If something isn't a HELL YES, it's a no. Your calendar gets 80% clearer overnight.

Number 3: Kill your to-do list. Replace it with a "Top 3" list. What are the 3 things that MUST get done today? Everything else is optional.

Number 4: Time block every single hour. No room for "I'll figure it out later." Sounds rigid but it's why I actually finish things now.

Number 5: Do weekly reviews every Friday. What worked? What didn't? Double down on what works. Kill what doesn't.

✨ CTA (45-60 seconds)
Real productivity isn't hustle culture — it's focus culture. Try the 2-hour rule tomorrow morning and watch what happens. Drop a 🔥 if you're going to try it!

HASHTAGS:
#productivity #productivityhacks #timemanagement #productivitytips #worksmart #deepwork #focusmode #entrepreneurship #businesstips #lifehacks #productivityboost #workfromhome #remotework #sidehustle #personaldevelopment #successmindset #goalsetting #motivation #hustleculture #entrepreneur #productivitytools #timeblocking #morningroutine #getthingsdone #productivity101`,

    reels: {
      title: "5 Productivity Hacks That Actually Work (Not Clickbait)",
      description: "I tried every productivity tip for 2 years and only 5 actually worked. The 2-hour rule alone tripled my output in 30 days. 🚀 Which one are you trying first? Comment below! Follow @threadangle for more productivity & growth tips.",
      hashtags: "#productivity #productivityhacks #productivitytips #timemanagement #worksmart #deepwork #focusmode #entrepreneur #businesstips #lifehacks #productivityboost #workfromhome #remotework #sidehustle #personaldevelopment #successmindset #goalsetting #motivation #hustleculture #productiv #timeblocking #morningroutine #getthingsdone #productivitytool #growthmindset #entrepreneurlife #worklife #success #goals #hustletips"
    },

    shorts: {
      title: "5 Productivity Hacks That Changed My Life",
      description: "Real productivity isn't hustle culture — it's focus culture. Try the 2-hour deep work rule and watch your output triple. Subscribe for more productivity & business tips!",
      tags: "productivity tips, productivity hacks, time management, deep work, focus, work smarter, time blocking, morning routine, productivity boost, entrepreneur tips, business productivity, shorts"
    }
  };

  const handleGenerate = () => {
    setIsGenerating(true);
    // Fake loading animation
    setTimeout(() => {
      setIsGenerating(false);
      setStep(2);
    }, 3000);
  };

  const handleStartAgain = () => {
    setStep(1);
    setActivePlatform('twitter');
  };

  return (
    <div className="min-h-screen bg-[#09090B] text-white">
      <Navbar />
      
      <div className="pt-24 pb-20 px-6 max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full mb-6">
            <span className="text-blue-400 text-sm font-medium">🎬 Interactive Dashboard Preview</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            See the Generate Workflow Before You Sign Up
          </h1>
          <p className="text-xl text-gray-400">
            Exactly how Threadangle turns one input into platform-ready content.
          </p>
        </div>

        {/* Demo Container */}
        <div className="max-w-4xl mx-auto">
          
          {step === 1 && (
            <div className="space-y-6">
              
              {/* Input Section */}
              <div className="bg-[#18181B] border border-[#27272A] rounded-xl p-8">
                <label className="block text-sm font-medium text-gray-400 mb-3">
                  📝 Step 1: Paste Your Content
                </label>
                <input
                  type="text"
                  value={sampleURL}
                  readOnly
                  className="w-full px-4 py-3 bg-[#09090B] border border-[#27272A] rounded-lg text-white cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-2">
                  ℹ️ This is a demo with pre-filled content
                </p>
              </div>

              {/* Platform Selection */}
              <div className="bg-[#18181B] border border-[#27272A] rounded-xl p-8">
                <label className="block text-sm font-medium text-gray-400 mb-4">
                  🎯 Step 2: Select Platforms
                </label>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  {[
                    { name: 'Twitter', platform: 'twitter', activeClass: 'border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/20' },
                    { name: 'LinkedIn', platform: 'linkedin', activeClass: 'border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/20' },
                    { name: 'TikTok', platform: 'tiktok', activeClass: 'border-pink-500 bg-pink-500/10 shadow-lg shadow-pink-500/20' },
                    { name: 'Reels', platform: 'reels', activeClass: 'border-purple-500 bg-purple-500/10 shadow-lg shadow-purple-500/20' },
                    { name: 'Shorts', platform: 'shorts', activeClass: 'border-red-500 bg-red-500/10 shadow-lg shadow-red-500/20' }
                  ].map(platform => (
                    <div
                      key={platform.name}
                      className={`relative flex flex-col items-center gap-2 p-4 border-2 rounded-lg cursor-not-allowed ${platform.activeClass}`}
                    >
                      <span className="text-2xl"><SocialPlatformIcon platform={platform.platform} className="w-6 h-6" /></span>
                      <span className="text-sm font-medium">{platform.name}</span>
                      <div className="absolute -top-2 -right-2 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full py-4 bg-blue-600 hover:bg-blue-700 rounded-xl font-bold text-lg shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
              >
                {isGenerating ? (
                  <span className="flex items-center justify-center gap-3">
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Generating Content...
                  </span>
                ) : (
                  '⚡ Generate Content (Demo)'
                )}
              </button>
              
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              
              {/* Platform Tabs */}
              <div className="bg-[#18181B] border border-[#27272A] rounded-xl overflow-hidden">
                <div className="flex border-b border-[#27272A] overflow-x-auto">
                  {[
                    { key: 'twitter', label: 'Twitter', platform: 'twitter' },
                    { key: 'linkedin', label: 'LinkedIn', platform: 'linkedin' },
                    { key: 'tiktok', label: 'TikTok', platform: 'tiktok' },
                    { key: 'reels', label: 'Reels', platform: 'reels' },
                    { key: 'shorts', label: 'Shorts', platform: 'shorts' }
                  ].map(platform => (
                    <button
                      key={platform.key}
                      onClick={() => setActivePlatform(platform.key)}
                      className={`flex items-center gap-2 px-6 py-4 font-medium whitespace-nowrap transition-colors ${
                        activePlatform === platform.key
                          ? 'bg-[#09090B] text-white border-b-2 border-blue-500'
                          : 'text-gray-400 hover:text-white hover:bg-[#09090B]'
                      }`}
                    >
                      <SocialPlatformIcon platform={platform.platform} className="w-4 h-4" />
                      <span>{platform.label}</span>
                    </button>
                  ))}
                </div>

                {/* Content Display */}
                <div className="p-8">
                  
                  {(activePlatform === 'twitter' || activePlatform === 'linkedin' || activePlatform === 'tiktok') && (
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold">Generated Content</h3>
                        <button className="px-4 py-2 bg-[#27272A] hover:bg-[#3F3F46] rounded-lg text-sm font-medium transition-colors">
                          📋 Copy to Clipboard
                        </button>
                      </div>
                      <div className="bg-[#09090B] border border-[#27272A] rounded-lg p-6 whitespace-pre-wrap text-sm leading-relaxed text-gray-300">
                        {demoContent[activePlatform]}
                      </div>
                    </div>
                  )}

                  {activePlatform === 'reels' && (
                    <div className="space-y-6">
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-bold text-gray-400">Title</h4>
                          <button className="px-3 py-1 bg-[#27272A] hover:bg-[#3F3F46] rounded text-xs">Copy</button>
                        </div>
                        <div className="bg-[#09090B] border border-[#27272A] rounded-lg p-4 text-sm text-gray-300">
                          {demoContent.reels.title}
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-bold text-gray-400">Description</h4>
                          <button className="px-3 py-1 bg-[#27272A] hover:bg-[#3F3F46] rounded text-xs">Copy</button>
                        </div>
                        <div className="bg-[#09090B] border border-[#27272A] rounded-lg p-4 text-sm text-gray-300">
                          {demoContent.reels.description}
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-bold text-gray-400">Hashtags</h4>
                          <button className="px-3 py-1 bg-[#27272A] hover:bg-[#3F3F46] rounded text-xs">Copy</button>
                        </div>
                        <div className="bg-[#09090B] border border-[#27272A] rounded-lg p-4 text-sm text-gray-300">
                          {demoContent.reels.hashtags}
                        </div>
                      </div>
                    </div>
                  )}

                  {activePlatform === 'shorts' && (
                    <div className="space-y-6">
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-bold text-gray-400">Title</h4>
                          <button className="px-3 py-1 bg-[#27272A] hover:bg-[#3F3F46] rounded text-xs">Copy</button>
                        </div>
                        <div className="bg-[#09090B] border border-[#27272A] rounded-lg p-4 text-sm text-gray-300">
                          {demoContent.shorts.title}
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-bold text-gray-400">Description</h4>
                          <button className="px-3 py-1 bg-[#27272A] hover:bg-[#3F3F46] rounded text-xs">Copy</button>
                        </div>
                        <div className="bg-[#09090B] border border-[#27272A] rounded-lg p-4 text-sm text-gray-300">
                          {demoContent.shorts.description}
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-sm font-bold text-gray-400">Tags</h4>
                          <button className="px-3 py-1 bg-[#27272A] hover:bg-[#3F3F46] rounded text-xs">Copy</button>
                        </div>
                        <div className="bg-[#09090B] border border-[#27272A] rounded-lg p-4 text-sm text-gray-300">
                          {demoContent.shorts.tags}
                        </div>
                      </div>
                    </div>
                  )}

                </div>
              </div>

              {/* Info Banner */}
              <div className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 border border-blue-500/20 rounded-xl p-6 text-center">
                <h3 className="text-xl font-bold mb-2">You just saw the core workflow</h3>
                <p className="text-gray-400 mb-4">
                  Create a free account to generate real content from your own URLs, transcripts, and raw drafts.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-[#A1A1AA] mb-5">
                  <div className="bg-[#18181B] border border-[#27272A] rounded-lg px-3 py-2">Inline editing + history</div>
                  <div className="bg-[#18181B] border border-[#27272A] rounded-lg px-3 py-2">Calendar + scheduling</div>
                  <div className="bg-[#18181B] border border-[#27272A] rounded-lg px-3 py-2">5 platform outputs</div>
                </div>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                  <button
                    onClick={() => navigate('/signup')}
                    className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold shadow-lg shadow-blue-500/20 transition-all"
                  >
                    Create My Free Account
                  </button>
                  <button
                    onClick={handleStartAgain}
                    className="px-8 py-3 bg-[#27272A] hover:bg-[#3F3F46] rounded-lg font-medium transition-colors"
                  >
                    ↺ Watch Demo Again
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-4">
                  ✅ 5 free generations • No credit card required • Cancel anytime
                </p>
              </div>

            </div>
          )}
          
        </div>

        {/* ── Full Workflow Showcase ── */}
        <div className="mt-20">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 border border-purple-500/20 rounded-full mb-5">
              <span className="text-purple-400 text-sm font-medium">🔓 Full Member Workflow</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-3">Three things that separate members from everyone else</h2>
            <p className="text-gray-400 text-lg">The generate demo above is only step 2 of 4.</p>
          </div>

          <div className="space-y-6">

            {/* Feature 1: Voice Learning */}
            <div className="bg-[#18181B] border border-[#27272A] rounded-2xl overflow-hidden">
              <div className="p-8">
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-12 h-12 rounded-xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-2xl flex-shrink-0">🎤</div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-1">AI Learns Your Voice — Not Generic AI Tone</h3>
                    <p className="text-gray-400 text-sm">Paste 3 writing samples. ThreadAngle learns your vocabulary, rhythm, and opinions. Every generation after that sounds like <em>you</em>, not a robot.</p>
                  </div>
                </div>
                <div className="flex gap-2 mb-4">
                  <button
                    onClick={() => setVoiceTab('before')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${voiceTab === 'before' ? 'bg-[#27272A] text-white' : 'text-gray-500 hover:text-gray-300'}`}
                  >❌ Generic AI</button>
                  <button
                    onClick={() => setVoiceTab('after')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${voiceTab === 'after' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'text-gray-500 hover:text-gray-300'}`}
                  >✅ With Your Voice</button>
                </div>
                <div className="bg-[#09090B] border border-[#27272A] rounded-xl p-5 text-sm leading-relaxed min-h-[90px] transition-all">
                  {voiceTab === 'before' ? (
                    <span className="text-gray-500 italic">
                      &ldquo;Productivity is a multifaceted concept encompassing time management methodologies and cognitive optimization strategies that enable individuals to maximize their output efficacy in both professional and personal domains.&rdquo;
                    </span>
                  ) : (
                    <span className="text-gray-300">
                      &ldquo;Real talk — I tested every productivity system that went viral over two years. Most made me <em>busier</em>, not better. But 5 things actually changed how I work. One of them 3x&rsquo;d my output in 30 days.&rdquo;
                    </span>
                  )}
                </div>
                {voiceTab === 'after' && (
                  <p className="text-xs text-purple-400 mt-2 flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    Same topic. Same facts. Sounds like the author wrote it.
                  </p>
                )}
              </div>
            </div>

            {/* Feature 2: Schedule & Post */}
            <div className="bg-[#18181B] border border-[#27272A] rounded-2xl overflow-hidden">
              <div className="p-8">
                <div className="flex items-start gap-4 mb-8">
                  <div className="w-12 h-12 rounded-xl bg-blue-500/15 border border-blue-500/30 flex items-center justify-center text-2xl flex-shrink-0">📅</div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-1">Generate → Edit → Schedule → Published</h3>
                    <p className="text-gray-400 text-sm">After generating, pick a date and time. ThreadAngle either auto-posts via connected social accounts or emails you a ready-to-paste reminder — your choice.</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { icon: '⚡', title: 'Generate', desc: 'One input → 5 platform outputs in 20 sec' },
                    { icon: '✏️', title: 'Edit Inline', desc: "Tweak any platform's copy before scheduling" },
                    { icon: '📆', title: 'Schedule', desc: 'Pick date/time + which platforms to post to' },
                    { icon: '🚀', title: 'Published', desc: 'Auto-posted or email reminder with copy ready' },
                  ].map((s, i) => (
                    <div key={i} className="bg-[#09090B] border border-[#27272A] rounded-xl p-4">
                      <div className="text-xl mb-2">{s.icon}</div>
                      <p className="text-sm font-bold text-white mb-1">{s.title}</p>
                      <p className="text-xs text-gray-500 leading-snug">{s.desc}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex items-center gap-2 text-xs text-gray-500 bg-[#09090B] border border-[#27272A] rounded-xl p-3">
                  <svg className="w-4 h-4 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span>Connect Twitter, LinkedIn, Instagram, and TikTok once — then forget about it. ThreadAngle handles the rest.</span>
                </div>
              </div>
            </div>

            {/* Feature 3: AI Video Studio */}
            <div className="bg-[#18181B] border border-[#27272A] rounded-2xl overflow-hidden">
              <div className="p-8">
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/25 flex items-center justify-center flex-shrink-0 shadow-lg shadow-blue-500/10">
                    <svg className="w-7 h-7 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1.5">
                      <h3 className="text-xl font-bold text-white">AI Video Studio</h3>
                      <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full">Production</span>
                    </div>
                    <p className="text-gray-400 text-sm leading-relaxed">Claude plans your hook, body &amp; CTA with retention notes → drag-and-drop storyboard previewer for scene approval → RunwayML Gen 4.5 renders photorealistic clips → export-ready for TikTok, Reels &amp; Shorts.</p>
                  </div>
                </div>

                {/* 3-step pipeline */}
                <div className="grid grid-cols-3 gap-3 mb-6">
                  {[
                    { icon: '🤖', step: '01', title: 'Claude Plans', desc: 'Hook, body & CTA with script optimization, retention notes, and platform SEO metadata' },
                    { icon: '🎞️', step: '02', title: 'Preview & Approve', desc: 'Drag-and-drop storyboard — inspect and edit every scene before committing to render' },
                    { icon: '🎬', step: '03', title: 'RunwayML Gen 4.5 Renders', desc: 'AI video with characters, stock fusion, text overlays & auto-captioning' },
                  ].map((s) => (
                    <div key={s.step} className="p-4 rounded-xl bg-[#09090B] border border-[#27272A]">
                      <div className="text-xl mb-2">{s.icon}</div>
                      <div className="text-[10px] font-bold text-gray-600 uppercase tracking-wider mb-0.5">{s.step}</div>
                      <div className="text-sm font-semibold text-white mb-1">{s.title}</div>
                      <div className="text-xs text-gray-500 leading-snug">{s.desc}</div>
                    </div>
                  ))}
                </div>

                {/* Feature pills */}
                <div className="flex flex-wrap gap-2 mb-6">
                  {[
                    '🎬 RunwayML Gen 4.5',
                    '🤖 Claude Script Planner',
                    '🎭 Character System',
                    '🎞️ Storyboard Previewer',
                    '📱 TikTok · Reels · Shorts',
                    '🔤 Auto Captions + SRT',
                    '⚡ Batch Generation',
                    '📊 SEO Optimizer',
                  ].map((f) => (
                    <span key={f} className="text-xs px-3 py-1.5 bg-[#09090B] border border-[#27272A] rounded-full text-gray-400">{f}</span>
                  ))}
                </div>

                {/* Output checklist */}
                <div className="grid sm:grid-cols-2 gap-2">
                  {[
                    'Shot-by-shot storyboard with per-scene timing',
                    'RunwayML Gen 4.5 photorealistic clip render',
                    'AI character generation or upload your own photo',
                    'Faceless — no camera, no face, no crew needed',
                    'Auto SRT captions + synchronized text overlays',
                    'YouTube Shorts · Instagram Reels · TikTok MP4',
                    'Platform SEO metadata (titles, descriptions, tags)',
                    'Batch generation — queue multiple videos at once',
                  ].map((item) => (
                    <div key={item} className="flex items-center gap-2 text-sm text-gray-400">
                      <svg className="w-4 h-4 text-emerald-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>

          </div>

          <div className="mt-10 text-center">
            <button
              onClick={() => navigate('/signup')}
              className="px-10 py-4 bg-blue-600 hover:bg-blue-700 rounded-xl font-bold text-lg shadow-lg shadow-blue-500/20 transition-all"
            >
              Start Free — Unlock Everything
            </button>
            <p className="text-xs text-gray-500 mt-3">5 free generations • No card required • Cancel anytime</p>
          </div>
        </div>

      </div>

      <Footer />
    </div>
  );
};

export default DemoPage;
