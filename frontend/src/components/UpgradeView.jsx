import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useDialog } from '../context/DialogContext';
import { api } from '../utils/api';

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    price: '$12',
    period: '/mo',
    description: 'Perfect for creators getting started',
    features: [
      '50 generations / month',
      'Twitter, LinkedIn & TikTok',
      'All content tones',
      'Priority support',
    ],
    highlight: true,
    badge: 'MOST POPULAR',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$29',
    period: '/mo',
    description: 'For power users and agencies',
    features: [
      'Unlimited generations',
      'Twitter, LinkedIn & TikTok',
      'All content tones',
      'Priority support',
      'API access',
    ],
    highlight: false,
  },
];

export default function UpgradeView() {
  const { user } = useAuth();
  const { alert: showAlert } = useDialog();
  const usageCount = user?.usage_count ?? 0;
  const usageLimit = user?.usage_limit ?? 3;

  const handleUpgrade = async (planId) => {
    try {
      const d = await api.createCheckout(planId);
      window.location.href = d.url;
    } catch {
      await showAlert({
        title: 'Checkout Failed',
        message: 'Could not start checkout. Please try again.',
        confirmText: 'OK',
        tone: 'danger',
      });
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-8 space-y-8">
      <header className="text-center">
        <h2 className="text-3xl font-bold text-white mb-2">Upgrade Your Plan</h2>
        <p className="text-[#A1A1AA]">
          You've used{' '}
          <span className="text-white font-bold">{usageCount}</span>{' '}
          of{' '}
          <span className="text-white font-bold">{usageLimit}</span>{' '}
          free generations.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {PLANS.map(plan => (
          <div
            key={plan.id}
            className={`relative bg-[#18181B] rounded-2xl p-7 flex flex-col gap-5 ${
              plan.highlight
                ? 'border-2 border-[#3B82F6] shadow-xl shadow-[#3B82F6]/10'
                : 'border border-[#27272A]'
            }`}
          >
            {plan.badge && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#3B82F6] text-white text-[10px] font-black px-3 py-1 rounded-full tracking-widest">
                {plan.badge}
              </span>
            )}

            <div>
              <h3 className="text-white font-bold text-xl">{plan.name}</h3>
              <p className="text-[#71717A] text-sm mt-1">{plan.description}</p>
            </div>

            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-black text-white">{plan.price}</span>
              <span className="text-[#71717A] text-sm">{plan.period}</span>
            </div>

            <ul className="space-y-2.5 flex-1">
              {plan.features.map(f => (
                <li key={f} className="flex items-center gap-2.5 text-sm text-[#A1A1AA]">
                  <svg className="w-4 h-4 text-[#3B82F6] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                  {f}
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleUpgrade(plan.id)}
              className={`w-full py-3.5 rounded-xl font-bold text-sm transition-all ${
                plan.highlight
                  ? 'bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white shadow-lg shadow-[#3B82F6]/20'
                  : 'bg-[#27272A] hover:bg-[#3F3F46] text-white'
              }`}
            >
              Get {plan.name} →
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
