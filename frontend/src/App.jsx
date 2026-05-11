import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { useAuth } from './context/AuthContext';
import Landing from './pages/Landing';
import DemoPage from './pages/DemoPage';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Contact from './pages/Contact';
import Blog from './pages/Blog';
import BlogPost from './pages/BlogPost';
import Admin from './pages/Admin';
import PricingPage from './pages/PricingPage';
import PrivacyPolicy from './pages/PrivacyPolicy';
import TermsOfService from './pages/TermsOfService';
import About from './pages/About';
import ScrollToTop from './components/ScrollToTop';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import History from './components/History';
import Calendar from './components/Calendar';
import UpgradeView from './components/UpgradeView';
import Settings from './components/Settings';
import Onboarding from './components/Onboarding';
import AnnouncementBar from './components/AnnouncementBar';
import { useWindowWidth } from './hooks/useWindowWidth';
import ThreadangleLogo from './components/ThreadangleLogo';
import CookieConsent from './components/CookieConsent';
import NotFound from './pages/NotFound';
import FacebookCallback from './pages/FacebookCallback';
import OAuthCallback from './pages/OAuthCallback';
import OAuthTestPage from './pages/OAuthTestPage';
import ErrorBoundary from './components/ErrorBoundary';
import { DialogProvider } from './context/DialogContext';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen bg-[#09090B] flex items-center justify-center text-white">Loading...</div>;
  return user ? children : <Navigate to="/login" />;
};

const BetaWaitlist = () => {
  const { user, logout } = useAuth();
  const message = user?.beta_waitlist_message || 'Thank you for signing up. Threadangle is currently in private beta testing. You have been added to our priority waitlist. Our admin will contact you shortly, and we will email you once Threadangle officially opens.';

  return (
    <div className="min-h-screen bg-[#09090B] text-white flex items-center justify-center px-5">
      <div className="w-full max-w-xl border border-[#27272A] bg-[#111113] rounded-lg p-8">
        <ThreadangleLogo size={36} showText={true} textSize={20} />
        <h1 className="mt-8 text-2xl font-bold">Private beta waitlist</h1>
        <p className="mt-4 text-[#D4D4D8] leading-relaxed">{message}</p>
        <p className="mt-4 text-sm text-[#8B949E]">Signed in as {user?.email}</p>
        <button
          onClick={logout}
          className="mt-8 px-4 py-2 rounded-lg border border-[#27272A] bg-[#18181B] text-[#E4E4E7] hover:text-white hover:bg-[#27272A] transition-colors"
        >
          Sign out
        </button>
      </div>
    </div>
  );
};

const DashboardLayout = () => {
    const [activeTab, setActiveTab] = useState('dashboard');
    const { user, loading } = useAuth();
    const [showOnboarding, setShowOnboarding] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const width = useWindowWidth();
    const isMobile = width < 768;

    useEffect(() => {
        if (!user) return;
        // Show onboarding if server flag says incomplete, OR if URL has ?onboarding=true
        const urlParams = new URLSearchParams(window.location.search);
        const urlOnboarding = urlParams.get('onboarding') === 'true';
        if (!user.onboarding_completed || urlOnboarding) {
            setShowOnboarding(true);
            // Clean up the URL param without triggering navigation
            if (urlOnboarding) {
                window.history.replaceState({}, '', '/dashboard');
            }
        }
    }, [user]);

    if (loading) return null;
    if (user?.beta_waitlist_mode && !user?.beta_full_access) {
        return <BetaWaitlist />;
    }

    const handleTabChange = (tab) => {
        setActiveTab(tab);
        if (isMobile) setSidebarOpen(false);
    };

    useEffect(() => {
      const onExternalTabChange = (event) => {
        const nextTab = event?.detail;
        if (typeof nextTab === 'string' && nextTab.length > 0) {
          handleTabChange(nextTab);
        }
      };
      window.addEventListener('dashboard-change-tab', onExternalTabChange);
      return () => window.removeEventListener('dashboard-change-tab', onExternalTabChange);
    }, [isMobile]);

    return (
        <div className="flex h-screen bg-[#09090B]">
            {isMobile && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, height: '56px',
                    background: '#09090B', borderBottom: '1px solid #18181B',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '0 16px', zIndex: 100,
                }}>
                    <ThreadangleLogo size={28} showText={true} textSize={16} />
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        style={{ background: 'none', border: 'none', color: '#FAFAFA', cursor: 'pointer', fontSize: '20px', padding: '4px' }}
                    >
                        {sidebarOpen ? '✕' : '☰'}
                    </button>
                </div>
            )}
            <div style={{
                position: isMobile ? 'fixed' : 'relative',
                top: isMobile ? '56px' : 0,
                left: 0, bottom: 0, width: '256px',
                transform: isMobile && !sidebarOpen ? 'translateX(-100%)' : 'translateX(0)',
                transition: 'transform 0.25s ease',
                zIndex: isMobile ? 99 : 'auto',
                overflowY: 'auto',
            }}>
                <Sidebar activeTab={activeTab} setActiveTab={handleTabChange} />
            </div>
            {isMobile && sidebarOpen && (
                <div
                    onClick={() => setSidebarOpen(false)}
                    style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 98 }}
                />
            )}
            <main className="flex-1 overflow-y-auto" style={{ paddingTop: isMobile ? '56px' : 0 }}>
              {activeTab === 'dashboard' && <Dashboard mode="generate" />}
              {activeTab === 'ai-video' && <Dashboard mode="video" />}
                {activeTab === 'history' && <History />}
                {activeTab === 'calendar' && <Calendar />}
                {activeTab === 'upgrade' && <UpgradeView />}
                {activeTab === 'settings' && <Settings />}
            </main>
            {showOnboarding && <Onboarding onComplete={() => setShowOnboarding(false)} />}
        </div>
    );
};

import { useLocation } from 'react-router-dom';

const TitleUpdater = () => {
  const location = useLocation();
  
  useEffect(() => {
    const titles = {
      '/': 'Threadangle — Find the angle. Go viral.',
      '/dashboard': 'Dashboard — Threadangle',
      '/login': 'Login — Threadangle', 
      '/signup': 'Sign Up — Threadangle',
      '/pricing': 'Pricing — Threadangle',
      '/contact': 'Contact Us — Threadangle',
      '/blog': 'Blog — Threadangle',
      '/admin': 'Admin — Threadangle',
      '/forgot-password': 'Reset Password — Threadangle',
      '/reset-password': 'Reset Password — Threadangle'
    };
    document.title = titles[location.pathname] || 'Threadangle';
  }, [location]);
  
  return null;
};

function App() {
  const { user } = useAuth();
  const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  return (
    <ErrorBoundary>
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
    <DialogProvider>
    <Router>
      <AnnouncementBar />
      <ScrollToTop />
      <TitleUpdater />
      <Routes>
        <Route path="/" element={user ? <Navigate to="/dashboard" /> : <Landing />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login />} />
        <Route path="/signup" element={user ? <Navigate to="/dashboard" /> : <Signup />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/free-hook-generator" element={<Navigate to="/demo" replace />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/terms" element={<TermsOfService />} />
        <Route path="/about" element={<About />} />
        <Route path="/blog" element={<Blog />} />
        <Route path="/blog/:slug" element={<BlogPost />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/auth/facebook/callback" element={<FacebookCallback />} />
        <Route path="/auth/callback" element={<OAuthCallback />} />
        <Route
          path="/oauth-test"
          element={
            <PrivateRoute>
              <OAuthTestPage />
            </PrivateRoute>
          }
        />
        
        <Route 
          path="/dashboard" 
          element={
            <PrivateRoute>
              <DashboardLayout />
            </PrivateRoute>
          } 
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <CookieConsent />
    </Router>
    </DialogProvider>
    </GoogleOAuthProvider>
    </ErrorBoundary>
  );
}

export default App;
