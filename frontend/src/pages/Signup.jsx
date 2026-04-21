import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import GoogleAuthButton from '../components/GoogleAuthButton';
import ThreadangleLogo from '../components/ThreadangleLogo';

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const checkoutPlan = searchParams.get('checkoutPlan');
  const hasCheckoutPlan = checkoutPlan === 'solo' || checkoutPlan === 'founder';
  const postAuthPath = hasCheckoutPlan ? `/dashboard?checkoutPlan=${checkoutPlan}` : '/dashboard';
  const loginPath = hasCheckoutPlan ? `/login?checkoutPlan=${checkoutPlan}` : '/login';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await signup(email, password);
      navigate(postAuthPath);
    } catch (err) {
      setError(err.message || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] text-white font-sans flex flex-col">
      <Navbar />
      <div className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-4 duration-700">
          {/* Header */}
          <div className="text-center mb-8">
            <Link to="/" className="inline-flex items-center gap-2 mb-6">
              <ThreadangleLogo size={40} showText={true} textSize={22} />
            </Link>
            <h1 className="text-3xl font-bold mb-2">Start for free</h1>
            <p className="text-[#71717A] text-sm">Create your account. No credit card required.</p>
          </div>

          {/* Trust badge */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <span className="text-[#10B981] text-sm">✓</span>
            <span className="text-[#71717A] text-xs font-medium">Join 1,200+ creators saving 5+ hours/week</span>
          </div>

          {/* Form Card */}
          <div className="bg-[#111113] border border-[#27272A] rounded-2xl p-8 shadow-2xl">
            {/* Google OAuth */}
            <GoogleAuthButton
              label="Continue with Google"
              onSuccess={() => navigate(postAuthPath)}
            />

            {/* Divider */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '16px 0' }}>
              <div style={{ flex: 1, height: '1px', background: '#27272A' }} />
              <span style={{ color: '#71717A', fontSize: '13px' }}>or sign up with email</span>
              <div style={{ flex: 1, height: '1px', background: '#27272A' }} />
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-[#A1A1AA] uppercase tracking-wider mb-2">
                  Email address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full bg-[#18181B] border border-[#3F3F46] rounded-xl px-4 py-3.5 text-white placeholder:text-[#52525B] text-sm focus:outline-none focus:border-[#3B82F6] transition-all"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#A1A1AA] uppercase tracking-wider mb-2">
                  Password
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    required
                    className="w-full bg-[#18181B] border border-[#3F3F46] rounded-xl px-4 py-3.5 text-white placeholder:text-[#52525B] text-sm focus:outline-none focus:border-[#3B82F6] transition-all"
                    style={{ paddingRight: '60px' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#71717A', cursor: 'pointer', fontSize: '13px', fontWeight: 500 }}
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#A1A1AA] uppercase tracking-wider mb-2">
                  Confirm password
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    value={confirm}
                    onChange={e => setConfirm(e.target.value)}
                    placeholder="Repeat your password"
                    required
                    className="w-full bg-[#18181B] border border-[#3F3F46] rounded-xl px-4 py-3.5 text-white placeholder:text-[#52525B] text-sm focus:outline-none focus:border-[#3B82F6] transition-all"
                    style={{ paddingRight: '60px' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#71717A', cursor: 'pointer', fontSize: '13px', fontWeight: 500 }}
                  >
                    {showConfirm ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-3 rounded-xl">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#3B82F6] hover:bg-[#3B82F6]/90 disabled:opacity-50 text-white font-bold py-4 rounded-xl text-sm transition-all shadow-lg shadow-[#3B82F6]/20 mt-2"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    Creating account...
                  </span>
                ) : 'Create Free Account'}
              </button>

              <p className="text-center text-[#52525B] text-xs mt-3">
                By signing up, you agree to our{' '}
                <a href="/terms" target="_blank" rel="noopener noreferrer" style={{ color: '#71717A', textDecoration: 'underline' }}>Terms</a>
                {' '}and{' '}
                <a href="/privacy" target="_blank" rel="noopener noreferrer" style={{ color: '#71717A', textDecoration: 'underline' }}>Privacy Policy</a>
              </p>
            </form>
          </div>

          <p className="text-center mt-6 text-sm text-[#71717A]">
            Already have an account?{' '}
            <Link to={loginPath} className="text-[#3B82F6] hover:text-[#3B82F6]/80 font-semibold transition-colors">
              Sign in →
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
