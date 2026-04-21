import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import ThreadangleLogo from './ThreadangleLogo';
import { useAuth } from '../context/AuthContext';
import { useCMS } from '../hooks/useCMS';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [avatarOpen, setAvatarOpen] = useState(false);
  const avatarRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { content: global } = useCMS('global', {
    navbar_signin_text: 'Sign In',
    navbar_cta_text: 'Start Free',
  });

  const handleAnchorClick = (e, targetId) => {
    e.preventDefault();
    if (window.location.pathname !== '/') {
      navigate('/' + targetId);
    } else {
      const element = document.querySelector(targetId);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
    setIsOpen(false);
  };

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (isOpen && !e.target.closest('nav')) setIsOpen(false);
      if (avatarOpen && avatarRef.current && !avatarRef.current.contains(e.target)) setAvatarOpen(false);
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [isOpen, avatarOpen]);

  const isActive = (path) => {
    if (path === '/') return location.hash === '';
    if (path.startsWith('/blog')) return location.pathname.startsWith('/blog');
    return location.pathname === path;
  };

  const userInitial = user?.name ? user.name[0].toUpperCase() : user?.email ? user.email[0].toUpperCase() : '?';

  const handleLogout = () => {
    logout();
    setAvatarOpen(false);
    navigate('/');
  };

  return (
    <nav className="sticky top-0 z-[100] border-b border-[#27272A] bg-[rgba(9,9,11,0.85)] backdrop-blur-[12px] h-[64px] flex items-center justify-between px-6">
      <Link to="/" className="flex items-center" onClick={() => setIsOpen(false)}>
        <ThreadangleLogo size={36} showText={true} textSize={18} />
      </Link>
      
      {/* Desktop Links */}
      <div className="hidden md:flex items-center gap-8 font-medium text-sm text-[#A1A1AA]">
        <a href="#features" onClick={(e) => handleAnchorClick(e, '#features')} className="hover:text-white transition-colors">Features</a>
        <Link to="/demo" className={`hover:text-white transition-colors ${isActive('/demo') ? 'text-[#3B82F6] border-b-2 border-[#3B82F6] pb-1 -mb-1' : ''}`}>Demo</Link>
        <Link to="/pricing" className={`hover:text-white transition-colors ${isActive('/pricing') ? 'text-[#3B82F6] border-b-2 border-[#3B82F6] pb-1 -mb-1' : ''}`}>Pricing</Link>
        <Link to="/blog" className={`hover:text-white transition-colors ${isActive('/blog') ? 'text-[#3B82F6] border-b-2 border-[#3B82F6] pb-1 -mb-1' : ''}`}>Blog</Link>
        <Link to="/contact" className={`hover:text-white transition-colors ${isActive('/contact') ? 'text-[#3B82F6] border-b-2 border-[#3B82F6] pb-1 -mb-1' : ''}`}>Contact</Link>
      </div>

      {/* Desktop Buttons */}
      <div className="hidden md:flex items-center gap-4">
        {user ? (
          <div className="relative" ref={avatarRef}>
            <button
              onClick={() => setAvatarOpen(!avatarOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#27272A]/50 transition-all"
            >
              <div className="w-8 h-8 rounded-full bg-[#3B82F6] flex items-center justify-center text-white font-bold text-sm">
                {userInitial}
              </div>
              <span className="text-white text-sm font-medium max-w-[120px] truncate">
                {user.name || user.email}
              </span>
              <svg className={`w-4 h-4 text-[#A1A1AA] transition-transform ${avatarOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {avatarOpen && (
              <div className="absolute right-0 mt-2 w-52 bg-[#18181B] border border-[#27272A] rounded-xl shadow-2xl py-2 z-50">
                <div className="px-4 py-2 border-b border-[#27272A]">
                  <p className="text-white font-semibold text-sm truncate">{user.name || 'User'}</p>
                  <p className="text-[#A1A1AA] text-xs truncate">{user.email}</p>
                </div>
                <Link
                  to="/dashboard"
                  onClick={() => setAvatarOpen(false)}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-[#A1A1AA] hover:text-white hover:bg-[#27272A]/50 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
                  Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                  Sign Out
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
            <Link to="/login" className="px-4 py-2 border border-[#27272A] text-white hover:bg-[#27272A]/50 rounded-lg text-sm font-bold transition-all">
              {global.navbar_signin_text}
            </Link>
            <Link to="/signup" className="px-4 py-2 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-[#3B82F6]/20">
              {global.navbar_cta_text}
            </Link>
          </>
        )}
      </div>

      {/* Mobile Menu Button */}
      <button 
        className="md:hidden text-[#A1A1AA] hover:text-white p-2"
        onClick={(e) => { e.stopPropagation(); setIsOpen(!isOpen); }}
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {isOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
        </svg>
      </button>

      {/* Mobile Dropdown */}
      {isOpen && (
        <div className="absolute top-[64px] left-0 w-full bg-[rgba(9,9,11,0.95)] backdrop-blur-[12px] border-b border-[#27272A] flex flex-col p-4 gap-4 md:hidden shadow-2xl">
          <a href="#features" className="text-[#A1A1AA] hover:text-white font-medium pl-2" onClick={(e) => handleAnchorClick(e, '#features')}>Features</a>
          <Link to="/demo" className={`font-medium pl-2 ${isActive('/demo') ? 'text-[#3B82F6]' : 'text-[#A1A1AA] hover:text-white'}`} onClick={() => setIsOpen(false)}>Demo</Link>
          <Link to="/pricing" className={`font-medium pl-2 ${isActive('/pricing') ? 'text-[#3B82F6]' : 'text-[#A1A1AA] hover:text-white'}`} onClick={() => setIsOpen(false)}>Pricing</Link>
          <Link to="/blog" className={`font-medium pl-2 ${isActive('/blog') ? 'text-[#3B82F6]' : 'text-[#A1A1AA] hover:text-white'}`} onClick={() => setIsOpen(false)}>Blog</Link>
          <Link to="/contact" className={`font-medium pl-2 ${isActive('/contact') ? 'text-[#3B82F6]' : 'text-[#A1A1AA] hover:text-white'}`} onClick={() => setIsOpen(false)}>Contact</Link>
          <div className="h-px bg-[#27272A] w-full my-2"></div>
          {user ? (
            <>
              <Link to="/dashboard" className="text-center py-3 border border-[#27272A] text-white rounded-lg font-bold" onClick={() => setIsOpen(false)}>Dashboard</Link>
              <button onClick={() => { handleLogout(); setIsOpen(false); }} className="text-center py-3 text-red-400 border border-red-500/30 rounded-lg font-bold">Sign Out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-center py-3 border border-[#27272A] text-white rounded-lg font-bold" onClick={() => setIsOpen(false)}>Sign In</Link>
              <Link to="/signup" className="text-center py-3 bg-[#3B82F6] text-white rounded-lg font-bold shadow-lg shadow-[#3B82F6]/20" onClick={() => setIsOpen(false)}>{global.navbar_cta_text}</Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
