import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import GoogleAuthButton from '../components/GoogleAuthButton';
import ThreadangleLogo from '../components/ThreadangleLogo';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const checkoutPlan = searchParams.get('checkoutPlan');
  const hasCheckoutPlan = checkoutPlan === 'solo' || checkoutPlan === 'founder';
  const postAuthPath = hasCheckoutPlan ? `/dashboard?checkoutPlan=${checkoutPlan}` : '/dashboard';
  const signupPath = hasCheckoutPlan ? `/signup?checkoutPlan=${checkoutPlan}` : '/signup';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate(postAuthPath);
    } catch (err) {
      setError(err.message || 'Invalid email or password.');
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
            <h1 className="text-3xl font-bold mb-2">Welcome back</h1>
            <p className="text-[#71717A] text-sm">Sign in to your Threadangle account</p>
          </div>

          {/* Value reminder */}
          <p style={{ textAlign: 'center', color: '#71717A', fontSize: '14px', marginBottom: '24px', lineHeight: 1.5 }}>
            ⚡ Turn any content into viral Twitter threads,<br />LinkedIn posts, and TikTok scripts in 20 seconds
          </p>

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
              <span style={{ color: '#71717A', fontSize: '13px' }}>or sign in with email</span>
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
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-semibold text-[#A1A1AA] uppercase tracking-wider">
                    Password
                  </label>
                  <Link to="/forgot-password" className="text-xs text-[#3B82F6] hover:text-[#3B82F6]/80 transition-colors font-medium">
                    Forgot password?
                  </Link>
                </div>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••"
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
                    Signing in...
                  </span>
                ) : 'Sign In'}
              </button>
            </form>
          </div>

          <p className="text-center mt-6 text-sm text-[#71717A]">
            Don't have an account?{' '}
            <Link to={signupPath} className="text-[#3B82F6] hover:text-[#3B82F6]/80 font-semibold transition-colors">
              Sign up free →
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
