import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import GoogleAuthButton from './GoogleAuthButton';
import ThreadangleLogo from './ThreadangleLogo';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SignupModal = ({ isOpen, onClose }) => {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [status, setStatus] = useState('idle'); // idle | loading | success | error
    const [errorMsg, setErrorMsg] = useState('');

    // Reset form when modal opens
    useEffect(() => {
        if (isOpen) {
            setEmail('');
            setPassword('');
            setStatus('idle');
            setErrorMsg('');
        }
    }, [isOpen]);

    // Close on Escape key
    useEffect(() => {
        if (!isOpen) return;
        const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [isOpen, onClose]);

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    const handleSignup = async () => {
        setErrorMsg('');
        if (!emailRegex.test(email)) {
            setErrorMsg('Please enter a valid email address.');
            return;
        }
        if (password.length < 6) {
            setErrorMsg('Password must be at least 6 characters.');
            return;
        }
        setStatus('loading');
        try {
            const res = await fetch(`${API_BASE}/api/auth/signup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            const data = await res.json();
            if (res.ok && (data.access_token || data.success)) {
                if (data.access_token) {
                    localStorage.setItem('token', data.access_token);
                }
                setStatus('success');
                setTimeout(() => {
                    onClose();
                    navigate('/dashboard');
                }, 800);
            } else {
                setStatus('idle');
                setErrorMsg(data.detail || data.message || 'Signup failed. Please try again.');
            }
        } catch {
            setStatus('idle');
            setErrorMsg('Network error. Please try again.');
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleSignup();
    };

    if (!isOpen) return null;

    return (
        <div
            style={{
                position: 'fixed', inset: 0, zIndex: 1000,
                background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(6px)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                padding: '24px',
            }}
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div
                style={{
                    background: '#18181B', border: '1px solid #27272A',
                    borderRadius: '24px', padding: '40px 36px',
                    width: '100%', maxWidth: '420px',
                    position: 'relative', boxShadow: '0 24px 60px rgba(0,0,0,0.6)',
                }}
            >
                {/* Close button */}
                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute', top: '16px', right: '16px',
                        background: 'none', border: 'none', color: '#71717A',
                        fontSize: '22px', cursor: 'pointer', lineHeight: 1,
                        padding: '4px 8px', borderRadius: '6px',
                    }}
                    aria-label="Close"
                >
                    ×
                </button>

                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: '28px' }}>
                    <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'center' }}>
                        <ThreadangleLogo size={36} showText={false} />
                    </div>
                    <h2 style={{ color: '#FAFAFA', fontSize: '22px', fontWeight: 700, margin: '0 0 8px' }}>
                        Start for free
                    </h2>
                    <p style={{ color: '#71717A', fontSize: '14px', margin: 0 }}>
                        Generate viral posts in 20 seconds
                    </p>
                </div>

                {status === 'success' ? (
                    <div style={{ textAlign: 'center', padding: '20px 0' }}>
                        <div style={{ fontSize: '40px', marginBottom: '12px' }}>✅</div>
                        <p style={{ color: '#10B981', fontWeight: 600, fontSize: '16px' }}>Account created! Redirecting…</p>
                    </div>
                ) : (
                    <>
                        {/* Google OAuth */}
                        <GoogleAuthButton
                            label="Continue with Google"
                            onSuccess={(data) => {
                                onClose();
                                navigate(data.is_new_user ? '/dashboard?onboarding=true' : '/dashboard');
                            }}
                        />

                        {/* Divider */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '16px 0' }}>
                            <div style={{ flex: 1, height: '1px', background: '#27272A' }} />
                            <span style={{ color: '#71717A', fontSize: '13px' }}>or sign up with email</span>
                            <div style={{ flex: 1, height: '1px', background: '#27272A' }} />
                        </div>

                        {/* Email */}
                        <div style={{ marginBottom: '16px' }}>
                            <input
                                type="email"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="your@email.com"
                                disabled={status === 'loading'}
                                style={{
                                    width: '100%', background: '#0F0F0F',
                                    border: '1px solid #3F3F46', borderRadius: '12px',
                                    padding: '14px 16px', color: '#FAFAFA',
                                    fontSize: '15px', outline: 'none',
                                    boxSizing: 'border-box',
                                    opacity: status === 'loading' ? 0.6 : 1,
                                }}
                            />
                        </div>

                        {/* Password */}
                        <div style={{ marginBottom: '20px', position: 'relative' }}>
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Password (min. 6 characters)"
                                disabled={status === 'loading'}
                                style={{
                                    width: '100%', background: '#0F0F0F',
                                    border: '1px solid #3F3F46', borderRadius: '12px',
                                    padding: '14px 60px 14px 16px', color: '#FAFAFA',
                                    fontSize: '15px', outline: 'none',
                                    boxSizing: 'border-box',
                                    opacity: status === 'loading' ? 0.6 : 1,
                                }}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#71717A', cursor: 'pointer', fontSize: '13px', fontWeight: 500 }}
                            >
                                {showPassword ? 'Hide' : 'Show'}
                            </button>
                        </div>

                        {/* Error message */}
                        {errorMsg && (
                            <p style={{ color: '#EF4444', fontSize: '13px', marginBottom: '16px', marginTop: '-8px' }}>
                                {errorMsg}
                            </p>
                        )}

                        {/* Submit button */}
                        <button
                            onClick={handleSignup}
                            disabled={status === 'loading'}
                            style={{
                                width: '100%', background: '#3B82F6',
                                color: '#FAFAFA', fontWeight: 700,
                                fontSize: '15px', padding: '14px',
                                borderRadius: '12px', border: 'none',
                                cursor: status === 'loading' ? 'not-allowed' : 'pointer',
                                opacity: status === 'loading' ? 0.7 : 1,
                                transition: 'opacity 0.2s',
                            }}
                        >
                            {status === 'loading' ? 'Creating account…' : 'Create free account'}
                        </button>

                        <p style={{ textAlign: 'center', color: '#52525B', fontSize: '12px', marginTop: '16px', marginBottom: 0 }}>
                            Already have an account?{' '}
                            <a href="/login" style={{ color: '#3B82F6', textDecoration: 'none' }}>Log in</a>
                        </p>
                    </>
                )}
            </div>
        </div>
    );
};

export default SignupModal;
