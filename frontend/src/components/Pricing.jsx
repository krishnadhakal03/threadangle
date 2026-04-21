import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useDialog } from '../context/DialogContext';
import { useCMS } from '../hooks/useCMS';
import { useSEO } from '../hooks/useSEO';
import Navbar from './Navbar';
import Footer from './Footer';

export default function Pricing() {
  const [loading, setLoading] = useState(null);
  const [openFaq, setOpenFaq] = useState(null);
  const navigate = useNavigate();
  const { user } = useAuth();
  const { alert: showAlert } = useDialog();
  
  const { content } = useCMS('pricing', {
    pricing_headline: "Simple, Transparent Pricing",
    pricing_subheadline: "Start free. Upgrade when you are ready. Cancel anytime.",
    pricing_plans: [
      {
        name: 'Free',
        planId: 'free',
        price: '$0',
        unit: '',
        description: 'Perfect for getting started.',
        features: ['5 free generations', 'Twitter threads', 'LinkedIn posts', 'No credit card required'],
        button: 'Get Started Free',
        popular: false,
        color: 'gray'
      },
      {
        name: 'Starter',
        planId: 'solo',
        price: '$12',
        unit: '/month',
        description: 'For creators who post consistently.',
        features: ['Unlimited generations', 'Twitter threads', 'LinkedIn posts', 'TikTok scripts', 'All 4 tones', 'Generation history', 'Email support'],
        button: 'Upgrade to Starter',
        popular: true,
        color: 'accent'
      },
      {
        name: 'Pro',
        planId: 'founder',
        price: '$19',
        unit: '/month',
        description: 'For power users and small teams.',
        features: ['Everything in Starter', 'Enhanced TikTok scripts with b-roll', 'Scene-by-scene video breakdowns', 'Priority generation queue', 'Early access to new features'],
        button: 'Upgrade to Pro',
        popular: false,
        color: 'accent'
      }
    ],
    pricing_comparison: [
      { name: 'Generations', f: '5 free', s: 'Unlimited', p: 'Unlimited' },
      { name: 'Twitter Threads', f: true, s: true, p: true },
      { name: 'LinkedIn Posts', f: true, s: true, p: true },
      { name: 'TikTok Scripts', f: false, s: true, p: true },
      { name: 'Instagram Reels', f: false, s: true, p: true },
      { name: 'YouTube Shorts', f: false, s: true, p: true },
      { name: 'Voice Learning', f: false, s: true, p: true },
      { name: 'Content History', f: false, s: true, p: true },
      { name: 'Auto-Scheduling', f: false, s: true, p: true },
      { name: 'Video Scripts', f: false, s: false, p: true },
      { name: 'Priority Queue', f: false, s: false, p: true }
    ],
    pricing_faqs: [
      { q: 'Can I switch plans later?', a: 'Yes. You can upgrade or downgrade at any time from your account Settings page. Changes take effect immediately.' },
      { q: 'What happens to my content if I cancel?', a: 'Your generated content history is saved for 30 days after cancellation. You can export it anytime before that.' },
      { q: 'Do you offer refunds?', a: 'We do not offer refunds on the current billing period but you can cancel anytime to stop future charges. No questions asked.' },
      { q: 'Is there a free trial for paid plans?', a: 'The free plan gives you 5 generations to try the product with no credit card required. That is your trial.' }
    ]
  });

  const { content: seo } = useCMS('seo', {
    pricing_meta_title: 'Pricing — Threadangle',
    pricing_meta_description: 'Simple, transparent pricing. Start free with 5 generations. Upgrade anytime. No contracts.'
  });

  useSEO({
    title: seo.pricing_meta_title,
    description: seo.pricing_meta_description,
  });
  const plans = Array.isArray(content.pricing_plans) ? content.pricing_plans : [];

  const handleUpgrade = async (plan) => {
    if (plan === 'free') return;

    if (!user) {
      navigate(`/signup?checkoutPlan=${plan}`);
      return;
    }

    setLoading(plan);
    try {
      navigate(`/dashboard?checkoutPlan=${plan}`);
    } catch (e) {
      await showAlert({
        title: 'Checkout Failed',
        message: 'Checkout failed: ' + e.message,
        confirmText: 'OK',
        tone: 'danger',
      });
    } finally {
      setLoading(null);
    }
  };

  const toggleFaq = (index) => {
    setOpenFaq(openFaq === index ? null : index);
  };

  const fAQs = Array.isArray(content.pricing_faqs) ? content.pricing_faqs : [];

  return (
    <div className="w-full">
      <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-800 pb-20">
        <header className="text-center space-y-2 mt-8">
          <h2 className="text-[40px] font-[700] text-[#FAFAFA] text-center">{content.pricing_headline}</h2>
          <p className="text-[18px] text-[#A1A1AA] text-center mt-2 font-medium">{content.pricing_subheadline}</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 px-6">
          {plans.map((plan) => (
            <div 
              key={plan.name} 
              className={`relative bg-card border ${plan.popular ? 'border-[#3B82F6] shadow-2xl shadow-[#3B82F6]/10 md:scale-105 z-10' : 'border-[#27272A]'} rounded-3xl p-8 flex flex-col glassmorphism transition-all md:hover:translate-y-[-4px]`}
            >
              {plan.popular && (
                <span className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-[#3B82F6] text-white text-[10px] font-black uppercase px-4 py-1.5 rounded-full tracking-widest shadow-lg">
                  MOST POPULAR
                </span>
              )}

              <div className="mb-8">
                <h3 className="text-xl font-bold text-white uppercase mb-2">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">{plan.price}</span>
                  {plan.unit && <span className="text-gray-500 font-bold uppercase text-sm">{plan.unit}</span>}
                </div>
                <p className="text-sm text-gray-500 mt-2 font-medium">{plan.description}</p>
              </div>

              <ul className="flex-1 space-y-4 mb-10">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm text-[#A1A1AA] font-medium leading-tight">
                    <span className="text-[#10B981] text-lg mt-[-2px]">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>

              <div className="flex flex-col gap-2">
                {plan.name === 'Free' ? (
                  <Link 
                    to="/signup"
                    className="w-full py-4 rounded-xl font-bold text-sm text-center transition-all bg-white text-black hover:bg-gray-200"
                  >
                    {plan.button}
                  </Link>
                ) : (
                  <button 
                    onClick={() => handleUpgrade(plan.planId)}
                    disabled={loading === plan.planId}
                    className={`w-full py-4 rounded-xl font-bold text-sm transition-all bg-[#3B82F6] text-white hover:bg-[#3B82F6]/90 shadow-xl shadow-[#3B82F6]/20 ${loading === plan.planId ? 'opacity-50 animate-pulse' : ''}`}
                  >
                    {loading === plan.planId ? 'Redirecting...' : plan.button}
                  </button>
                )}
                
                {(plan.name === 'Starter' || plan.name === 'Pro') && (
                  <p className="text-[12px] text-[#71717A] text-center w-full mt-2">
                    ✓ Cancel anytime · No contracts · Instant access
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Feature Comparison Table */}
        <div className="mt-24 px-6">
          <h2 className="text-2xl font-bold text-white text-center mb-8">Everything Compared</h2>
          <div className="w-full overflow-x-auto rounded-lg border border-[#27272A] bg-[#111113]">
            <table className="w-full text-sm text-left whitespace-nowrap">
              <thead className="bg-[#18181B] border-b border-[#27272A] text-[12px] uppercase text-[#71717A] tracking-wider font-bold">
                <tr>
                  <th className="px-6 py-5 sticky left-0 bg-[#18181B] z-10 w-1/3">Feature</th>
                  <th className="px-6 py-5 text-center text-white">Free</th>
                  <th className="px-6 py-5 text-center text-[#3B82F6]">Starter</th>
                  <th className="px-6 py-5 text-center text-[#8B5CF6]">Pro</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#27272A]">
                {(Array.isArray(content.pricing_comparison) ? content.pricing_comparison : []).map((row, i) => (
                  (() => {
                    const freeVal = row.f ?? row.free;
                    const starterVal = row.s ?? row.starter;
                    const proVal = row.p ?? row.pro;
                    return (
                  <tr key={i} className={i % 2 === 0 ? "bg-[#111113]" : "bg-[#18181B]"}>
                    <td className={`px-6 py-4 font-medium text-white sticky left-0 ${i % 2 === 0 ? "bg-[#111113]" : "bg-[#18181B]"} z-10border-r md:border-r-0 border-[#27272A] md:border-transparent block md:table-cell`}>
                      {row.name}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {typeof freeVal === 'boolean' ? (freeVal ? <span className="text-[#10B981] font-bold">✓</span> : <span className="text-[#3F3F46] font-bold">✗</span>) : <span className="text-gray-300">{freeVal}</span>}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {typeof starterVal === 'boolean' ? (starterVal ? <span className="text-[#10B981] font-bold">✓</span> : <span className="text-[#3F3F46] font-bold">✗</span>) : <span className="text-gray-300">{starterVal}</span>}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {typeof proVal === 'boolean' ? (proVal ? <span className="text-[#10B981] font-bold">✓</span> : <span className="text-[#3F3F46] font-bold">✗</span>) : <span className="text-gray-300">{proVal}</span>}
                    </td>
                  </tr>
                    );
                  })()
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pricing FAQ Section */}
        <div className="mt-24 max-w-3xl mx-auto px-6">
          <div className="text-center mb-10">
            <h2 className="text-2xl font-bold text-white mb-2">Pricing Questions</h2>
          </div>
          <div className="space-y-4">
            {fAQs.map((faq, index) => (
              <div 
                key={index}
                className="bg-[#111113] border border-[#27272A] rounded-2xl overflow-hidden cursor-pointer"
                onClick={() => toggleFaq(index)}
              >
                <div className="px-6 py-5 flex items-center justify-between">
                  <h3 className="text-base font-medium text-white select-none">{faq.q}</h3>
                  <div className={`transform transition-transform duration-300 flex items-center justify-center w-8 h-8 rounded-full bg-[#18181B] text-[#3B82F6] ${openFaq === index ? 'rotate-180' : ''}`}>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
                <div 
                  className={`px-6 text-[#A1A1AA] text-sm leading-relaxed transition-all duration-300 overflow-hidden ${
                    openFaq === index ? 'max-h-64 pb-6 opacity-100' : 'max-h-0 opacity-0'
                  }`}
                >
                  {faq.a}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
