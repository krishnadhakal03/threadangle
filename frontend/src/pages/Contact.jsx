import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';
import { useCMS } from '../hooks/useCMS';
import { useSEO } from '../hooks/useSEO';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SocialPlatformIcon from '../components/SocialPlatformIcon';

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: 'General Question',
    message: ''
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const { content: seo } = useCMS('seo', {
    contact_meta_title: 'Contact — Threadangle',
    contact_meta_description: 'Get in touch with the Threadangle team. We reply within 24 hours.'
  });

  const { content } = useCMS('contact', {
    contact_headline: "Get in Touch",
    contact_subheadline: "Have a question, feedback, or just want to say hello? We would love to hear from you.",
    contact_email: "hello@kriangle.com",
    contact_response_time: "Within 24 hours",
    contact_hours: "Monday to Saturday",
    contact_made_by: "Kriangle",
    twitter_url: 'https://twitter.com/threadangle',
    linkedin_url: 'https://linkedin.com/company/threadangle',
    tiktok_url: 'https://tiktok.com/@threadangle',
    contact_faqs: [
      { q: 'How do I cancel my subscription?', a: "Go to Settings → Manage Subscription. You'll be taken to the Stripe portal where you can cancel with one click." },
      { q: 'Why is my generation failing?', a: 'Make sure your URL is publicly accessible or try using raw text instead. YouTube transcripts require a publicly available video.' },
      { q: 'Can I get a refund?', a: "We don't offer refunds on the current billing period, but you can cancel anytime to stop future charges." }
    ]
  });

  useSEO({
    title: seo.contact_meta_title,
    description: seo.contact_meta_description,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.message.length < 20) {
      setError('Message must be at least 20 characters');
      return;
    }
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await api.submitContact(formData);
      setSuccess('Thanks! We will get back to you within 24 hours.');
      setFormData({ name: '', email: '', subject: 'General Question', message: '' });
    } catch (err) {
      setError('Something went wrong. Please try again or email us directly at hello@kriangle.com');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] text-white font-sans selection:bg-accent/30 selection:text-white block">
      <Navbar />
      <div className="max-w-6xl mx-auto pt-24 pb-20 px-6 text-center">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">{content.contact_headline}</h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">{content.contact_subheadline}</p>

        <div className="grid md:grid-cols-2 gap-12 mt-16 text-left">
          {/* Left: Contact Form */}
          <div className="bg-card/50 backdrop-blur-xl border border-border rounded-3xl p-8 md:p-10 shadow-2xl relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent opacity-50 pointer-events-none"></div>
            
            {success ? (
              <div className="flex flex-col items-center justify-center py-12 text-center space-y-4 relative z-10 animate-in fade-in zoom-in duration-500">
                <div className="w-20 h-20 bg-[#10B981]/10 text-[#10B981] rounded-full flex items-center justify-center text-4xl mb-2 shadow-[0_0_30px_rgba(16,185,129,0.2)]">✅</div>
                <h3 className="text-2xl font-bold text-white">Message Sent!</h3>
                <p className="text-[#A1A1AA] mb-8 max-w-sm">Thanks for reaching out. We will get back to you at {formData.email} within 24 hours.</p>
                <div className="flex flex-col gap-3 w-full max-w-xs mt-4">
                  <button type="button" onClick={() => setSuccess('')} className="w-full bg-[#18181B] border border-[#27272A] hover:border-[#3B82F6] text-white font-medium py-3 rounded-xl transition-all">Send Another Message</button>
                  <Link to="/dashboard" className="w-full bg-[#3B82F6] hover:bg-blue-600 text-white font-medium py-3 rounded-xl transition-all block text-center">Go to Dashboard →</Link>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-[12px] font-[600] text-[#A1A1AA] mb-1 ml-1">Name</label>
                    <input 
                      type="text" 
                      required
                      className="w-full bg-dark/60 border border-border rounded-xl p-4 text-white focus:border-accent outline-none transition-all placeholder:text-gray-700"
                      placeholder="Your Name"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-[12px] font-[600] text-[#A1A1AA] mb-1 ml-1">Email</label>
                    <input 
                      type="email" 
                      required
                      className="w-full bg-dark/60 border border-border rounded-xl p-4 text-white focus:border-accent outline-none transition-all placeholder:text-gray-700"
                      placeholder="you@email.com"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[12px] font-[600] text-[#A1A1AA] mb-1 ml-1">Subject</label>
                  <select 
                    className="w-full bg-[#18181B] border border-[#3F3F46] rounded-xl p-4 text-[#FAFAFA] focus:border-[#3B82F6] outline-none transition-all appearance-none cursor-pointer"
                    style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2371717A'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundPosition: 'right 1rem center', backgroundRepeat: 'no-repeat', backgroundSize: '1.5em 1.5em', paddingRight: '3rem' }}
                    value={formData.subject}
                    onChange={(e) => setFormData({...formData, subject: e.target.value})}
                  >
                    <option value="General Question">General Question</option>
                    <option value="Billing or Subscription">Billing or Subscription</option>
                    <option value="Bug Report">Bug Report</option>
                    <option value="Feature Request">Feature Request</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[12px] font-[600] text-[#A1A1AA] mb-1 ml-1">Message</label>
                  <textarea 
                    required
                    rows="5"
                    className="w-full bg-dark/60 border border-border rounded-xl p-4 text-white focus:border-accent outline-none transition-all placeholder:text-gray-700 resize-none"
                    placeholder="How can we help you?"
                    value={formData.message}
                    onChange={(e) => setFormData({...formData, message: e.target.value})}
                  ></textarea>
                  <p className={`text-[12px] font-medium mt-2 ml-1 ${
                    formData.message.length < 20 ? "text-[#EF4444]" : 
                    formData.message.length <= 50 ? "text-[#10B981]" : "text-[#71717A]"
                  }`}>
                    {formData.message.length < 20 
                      ? `${formData.message.length} characters — ${20 - formData.message.length} more needed` 
                      : formData.message.length <= 50
                      ? `${formData.message.length} characters \u2713 minimum met`
                      : `${formData.message.length} characters`}
                  </p>
                </div>

                {error && <div className="bg-[#EF4444]/10 border border-[#EF4444]/20 text-[#EF4444] text-sm p-4 rounded-xl mb-6 text-center">{error}</div>}

                <button 
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-[#3B82F6]/20 disabled:opacity-70 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      <span>Sending...</span>
                    </>
                  ) : (
                    'Send Message'
                  )}
                </button>
              </form>
            )}
          </div>

          {/* Right: Info */}
          <div className="space-y-3 flex flex-col justify-center">
            {/* Email Card */}
            <div className="bg-card/30 border border-border/50 rounded-2xl p-6 flex items-start gap-4 hover:border-accent/30 transition-all group w-full">
              <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center text-accent text-2xl group-hover:scale-110 transition-transform">✉️</div>
              <div>
                <p className="text-[12px] font-[600] text-[#A1A1AA] uppercase tracking-widest mb-1">Email Us</p>
                <p className="text-xl font-bold text-white mb-1">{content.contact_email}</p>
                <p className="text-xs text-[#71717A]">We reply within 24 hours</p>
              </div>
            </div>

            {/* Time Card */}
            <div className="bg-card/30 border border-border/50 rounded-2xl p-6 flex items-start gap-4 hover:border-accent/30 transition-all group w-full">
              <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center text-accent text-2xl group-hover:scale-110 transition-transform">🕒</div>
              <div>
                <p className="text-[12px] font-[600] text-[#A1A1AA] uppercase tracking-widest mb-1">Response Time</p>
                <p className="text-xl font-bold text-white mb-1">{content.contact_response_time}</p>
                <p className="text-xs text-[#71717A]">{content.contact_hours}</p>
              </div>
            </div>

            {/* Maker Card */}
            <div className="bg-card/30 border border-border/50 rounded-2xl p-6 flex items-start gap-4 hover:border-accent/30 transition-all group w-full">
              <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center text-accent text-2xl group-hover:scale-110 transition-transform">👤</div>
              <div>
                <p className="text-[12px] font-[600] text-[#A1A1AA] uppercase tracking-widest mb-1">Made by</p>
                <p className="text-xl font-bold text-white mb-1">{content.contact_made_by}</p>
                <p className="text-xs text-[#71717A]">A solo founder building in public</p>
              </div>
            </div>

            {/* Social Links */}
            <div className="mt-6 mb-2">
              <h4 className="text-[11px] font-bold text-[#A1A1AA] uppercase tracking-widest mb-3">Follow Us</h4>
              <div className="flex flex-wrap gap-3">
                <a href={content.twitter_url || 'https://twitter.com/threadangle'} target="_blank" rel="noreferrer" className="flex items-center gap-2 border border-[#27272A] hover:border-[#3B82F6] px-4 py-2 rounded-xl text-sm font-medium transition-colors">
                  <span>𝕏</span> @threadangle
                </a>
                <a href={content.linkedin_url || 'https://linkedin.com/company/threadangle'} target="_blank" rel="noreferrer" className="flex items-center gap-2 border border-[#27272A] hover:border-[#3B82F6] px-4 py-2 rounded-xl text-sm font-medium transition-colors">
                  <span className="text-[#0A66C2] font-bold"><SocialPlatformIcon platform="linkedin" className="w-4 h-4" /></span> Threadangle
                </a>
                <a href={content.tiktok_url || 'https://tiktok.com/@threadangle'} target="_blank" rel="noreferrer" className="flex items-center gap-2 border border-[#27272A] hover:border-[#3B82F6] px-4 py-2 rounded-xl text-sm font-medium transition-colors">
                  <span><SocialPlatformIcon platform="tiktok" className="w-4 h-4" /></span> @threadangle
                </a>
              </div>
            </div>

            {/* Billing Note Box */}
            <div className="bg-[#18181B] border border-[#27272A] border-l-[3px] border-l-[#3B82F6] rounded-lg p-5 mt-6">
              <p className="text-[13px] text-[#A1A1AA] mb-3 leading-relaxed">
                💳 Billing issue? You can manage or cancel your subscription directly from your account Settings page — no need to contact us.
              </p>
              <Link to="/dashboard" className="text-[13px] text-[#3B82F6] hover:underline font-medium">
                Go to Settings →
              </Link>
            </div>

            {/* Quick Answers */}
            <div className="mt-6 grid gap-4">
              {(Array.isArray(content.contact_faqs) ? content.contact_faqs : []).map((faq, idx) => (
                <div key={idx} className="bg-[#111113] border border-[#27272A] rounded-lg p-6 flex flex-col">
                  <h3 className="text-[14px] font-[600] text-white mb-2">{faq.q}</h3>
                  <p className="text-[13px] text-[#A1A1AA] leading-[1.6] mb-4">{faq.a}</p>
                  <Link to="/terms" className="text-[13px] text-[#3B82F6] hover:underline block mt-auto font-medium">
                    Learn more →
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
      <Footer />
    </div>
  );
};

export default Contact;
