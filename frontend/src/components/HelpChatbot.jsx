import React, { useState, useEffect, useRef } from 'react';

const HelpChatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: "Hi! 👋 I'm here to help. What do you need help with?",
      options: [
        "How do I generate content?",
        "Why did my generation fail?",
        "How does voice learning work?",
        "How do I schedule posts?",
        "What are the platform limits?"
      ]
    }
  ]);

  // Auto-scroll to newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const faqs = {
    "How do I generate content?": {
      answer: "It's easy! Just paste a URL or text, select your platforms (Twitter, LinkedIn, TikTok, etc.), and click 'Generate Content'. We'll create optimized content for each platform in ~20 seconds.",
      followUp: ["Why did my generation fail?", "How does voice learning work?"]
    },
    
    "Why did my generation fail?": {
      answer: "Common reasons:\n\n• YouTube video doesn't have captions\n• Website blocked our access (403 error)\n• Page doesn't exist (404 error)\n\nSolution: Try pasting the content as raw text instead, or use a different URL. Your credit is always refunded for failed generations.",
      followUp: ["How do I generate content?", "What are the platform limits?"]
    },
    
    "How does voice learning work?": {
      answer: "After your first 3 successful generations, we analyze your content to learn your unique writing style. From then on, all future content will sound more like YOU, not generic AI. Check your sidebar for 'Voice Learned' status!",
      followUp: ["How do I generate content?", "How do I schedule posts?"]
    },
    
    "How do I schedule posts?": {
      answer: "Go to History → Click '📅 Schedule' on any generation → Pick a date and time → We'll email you a reminder when it's time to post! Track everything in the Calendar tab.",
      followUp: ["How does voice learning work?", "What are the platform limits?"]
    },
    
    "What are the platform limits?": {
      answer: "We generate content for:\n\n• Twitter: 280 chars per tweet\n• LinkedIn: 3000 chars\n• TikTok: 2200 chars\n• Instagram Reels: 2200 chars\n• YouTube Shorts: 5000 chars\n\nYou can edit any content before copying!",
      followUp: ["How do I generate content?", "How do I schedule posts?"]
    }
  };
  
  const handleQuestionClick = (question) => {
    // Add user message
    setMessages(prev => [...prev, {
      type: 'user',
      text: question
    }]);
    
    // Add bot response
    setTimeout(() => {
      const response = faqs[question];
      setMessages(prev => [...prev, {
        type: 'bot',
        text: response.answer,
        options: response.followUp
      }]);
    }, 500);
  };
  
  const resetChat = () => {
    setMessages([{
      type: 'bot',
      text: "Hi! 👋 I'm here to help. What do you need help with?",
      options: Object.keys(faqs)
    }]);
  };
  
  return (
    <>
      {/* FAB trigger button */}
      <button
        onClick={() => setIsOpen(o => !o)}
        aria-label="Open support chat"
        className="fixed bottom-6 right-6 z-50 w-13 h-13 rounded-full shadow-xl flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95"
        style={{
          width: '52px', height: '52px',
          background: isOpen
            ? '#21262D'
            : 'linear-gradient(135deg, #1F6FEB 0%, #7C3AED 100%)',
          border: isOpen ? '1px solid #30363D' : 'none',
          boxShadow: isOpen ? 'none' : '0 4px 24px rgba(31,111,235,0.4)',
        }}
      >
        {isOpen ? (
          <svg className="w-5 h-5 text-[#8B949E]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )}
      </button>

      {/* Chat window */}
      {isOpen && (
        <div
          className="fixed bottom-24 right-6 z-50 flex flex-col overflow-hidden"
          style={{
            width: '360px', height: '480px',
            background: '#0D1117',
            border: '1px solid #21262D',
            borderRadius: '16px',
            boxShadow: '0 24px 64px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.03)',
          }}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-4 py-3 flex-shrink-0"
            style={{
              background: 'linear-gradient(135deg, #1F6FEB 0%, #7C3AED 100%)',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/15 backdrop-blur flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <div className="text-sm font-bold text-white leading-none">Threadangle Support</div>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[10px] text-white/70">Typically replies instantly</span>
                </div>
              </div>
            </div>
            <button
              onClick={resetChat}
              className="text-white/60 hover:text-white text-[11px] font-semibold px-2 py-1 rounded hover:bg-white/10 transition-colors"
            >
              Reset
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ scrollbarWidth: 'thin', scrollbarColor: '#21262D transparent' }}>
            {messages.map((msg, i) => (
              <div key={i}>
                {msg.type === 'bot' ? (
                  <div className="flex items-start gap-2.5">
                    <div
                      className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={{ background: 'linear-gradient(135deg, #1F6FEB, #7C3AED)' }}
                    >
                      <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div className="max-w-[82%]">
                      <div
                        className="rounded-2xl rounded-tl-sm px-3.5 py-2.5"
                        style={{ background: '#161B22', border: '1px solid #21262D' }}
                      >
                        <p className="text-sm text-[#C9D1D9] whitespace-pre-line leading-relaxed">{msg.text}</p>
                        {msg.options && (
                          <div className="mt-3 space-y-1.5">
                            {msg.options.map((option, j) => (
                              <button
                                key={j}
                                onClick={() => handleQuestionClick(option)}
                                className="block w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-[#388bfd] transition-colors"
                                style={{ background: 'rgba(31,111,235,0.08)', border: '1px solid rgba(31,111,235,0.2)' }}
                                onMouseEnter={e => e.currentTarget.style.background = 'rgba(31,111,235,0.16)'}
                                onMouseLeave={e => e.currentTarget.style.background = 'rgba(31,111,235,0.08)'}
                              >
                                {option}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-end">
                    <div
                      className="max-w-[72%] rounded-2xl rounded-tr-sm px-3.5 py-2.5"
                      style={{ background: '#1F6FEB' }}
                    >
                      <p className="text-sm text-white">{msg.text}</p>
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Footer */}
          <div
            className="px-4 py-3 flex-shrink-0 text-center"
            style={{ borderTop: '1px solid #21262D', background: '#0D1117' }}
          >
            <p className="text-[11px] text-[#484F58]">
              Need more help?{' '}
              <a href="mailto:info@kriangle.com" className="text-[#388bfd] hover:text-[#60CDFF] transition-colors">
                Email us
              </a>
            </p>
          </div>
        </div>
      )}
    </>
  );
};

export default HelpChatbot;
