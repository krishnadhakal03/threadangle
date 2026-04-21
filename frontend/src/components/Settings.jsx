import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useDialog } from '../context/DialogContext';
import { api } from '../utils/api';
import SocialConnections from './SocialConnections';

export default function Settings() {
  const { user, updateName, logout } = useAuth();
  const { alert: showAlert } = useDialog();
  const navigate = useNavigate();

  // Profile section
  const [name, setName] = useState(user?.name || '');
  const [nameSaving, setNameSaving] = useState(false);
  const [nameMsg, setNameMsg] = useState('');

  // Password section
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwSaving, setPwSaving] = useState(false);
  const [pwMsg, setPwMsg] = useState('');
  const [pwError, setPwError] = useState('');

  // Danger zone
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const planLimit = user?.plan === 'free' ? 5 : user?.plan === 'solo' ? 30 : user?.plan === 'founder' ? 100 : null;
  const usagePct = planLimit ? Math.min(((user?.usage_count ?? 0) / planLimit) * 100, 100) : 10;

  const handleSaveName = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setNameSaving(true);
    setNameMsg('');
    try {
      await updateName(name.trim());
      setNameMsg('Name updated successfully');
    } catch (err) {
      setNameMsg('Failed to update name');
    } finally {
      setNameSaving(false);
      setTimeout(() => setNameMsg(''), 3000);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwError('');
    setPwMsg('');
    if (newPw !== confirmPw) return setPwError('New passwords do not match');
    if (newPw.length < 8) return setPwError('Password must be at least 8 characters');
    setPwSaving(true);
    try {
      await api.changePassword(currentPw, newPw);
      setPwMsg('Password changed successfully');
      setCurrentPw('');
      setNewPw('');
      setConfirmPw('');
    } catch (err) {
      setPwError(err.message || 'Failed to change password');
    } finally {
      setPwSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'DELETE') return;
    setDeleting(true);
    try {
      await api.deleteAccount();
      logout();
      navigate('/');
    } catch (err) {
      setDeleting(false);
      await showAlert({
        title: 'Delete Failed',
        message: 'Failed to delete account. Please try again.',
        confirmText: 'OK',
        tone: 'danger',
      });
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-4 md:p-8 space-y-4 md:space-y-8">
      <header>
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-1">Settings</h2>
        <p className="text-[#A1A1AA]">Manage your account preferences</p>
      </header>

      {/* Profile */}
      <section className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6 space-y-5">
        <h3 className="text-white font-bold text-lg">Profile</h3>
        <div>
          <label className="block text-xs font-bold text-[#71717A] uppercase tracking-wider mb-1.5">Email</label>
          <input
            type="text"
            value={user?.email || ''}
            disabled
            className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-4 py-3 text-[#71717A] text-sm cursor-not-allowed"
          />
          <p className="text-[11px] text-[#52525B] mt-1">Email cannot be changed</p>
        </div>
        <form onSubmit={handleSaveName}>
          <label className="block text-xs font-bold text-[#71717A] uppercase tracking-wider mb-1.5">Display Name</label>
          <div className="flex gap-3">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              className="flex-1 bg-[#09090B] border border-[#27272A] rounded-xl px-4 py-3 text-white text-sm focus:border-[#3B82F6] outline-none transition-colors"
            />
            <button
              type="submit"
              disabled={nameSaving || !name.trim()}
              className="px-5 py-2 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white text-sm font-bold rounded-xl transition-all disabled:opacity-50"
            >
              {nameSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
          {nameMsg && <p className="text-green-400 text-xs mt-2 font-medium">{nameMsg}</p>}
        </form>
      </section>

      {/* Plan & Usage */}
      <section className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6 space-y-4">
        <h3 className="text-white font-bold text-lg">Plan &amp; Usage</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[#A1A1AA] text-sm">Current plan</p>
            <p className="text-white font-bold text-xl capitalize mt-0.5">{user?.plan || 'Free'}</p>
          </div>
          {user?.plan === 'free' && (
            <Link
              to="/pricing"
              className="px-5 py-2.5 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white text-sm font-bold rounded-xl transition-all shadow-lg shadow-[#3B82F6]/20"
            >
              Upgrade Plan →
            </Link>
          )}
        </div>
        <div>
          <div className="flex justify-between text-xs text-[#71717A] mb-2">
            <span>Generations used this period</span>
            <span className="font-bold">{user?.usage_count ?? 0} / {planLimit ?? '\u221e'} generations</span>
          </div>
          <div className="w-full bg-[#27272A] rounded-full h-2 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${usagePct >= 90 ? 'bg-red-500' : usagePct >= 70 ? 'bg-amber-500' : 'bg-[#3B82F6]'}`}
              style={{ width: `${usagePct}%` }}
            />
          </div>
        </div>
        {user?.plan !== 'free' && (
          <button
            onClick={() => api.getPortal().then(d => window.open(d.url, '_blank', 'noopener,noreferrer')).catch(() => showAlert({
              title: 'Billing Portal Unavailable',
              message: 'Could not open billing portal. Please try again.',
              confirmText: 'OK',
              tone: 'danger',
            }))}
            className="text-sm text-[#3B82F6] hover:text-[#60A5FA] font-medium transition-colors"
          >
            Manage billing →
          </button>
        )}
      </section>

      {/* Change Password — hidden for Google users */}
      {!user?.google_user && (
        <section className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6 space-y-4">
          <h3 className="text-white font-bold text-lg">Change Password</h3>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-[#71717A] uppercase tracking-wider mb-1.5">Current Password</label>
              <input
                type="password"
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-4 py-3 text-white text-sm focus:border-[#3B82F6] outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-[#71717A] uppercase tracking-wider mb-1.5">New Password</label>
              <input
                type="password"
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-4 py-3 text-white text-sm focus:border-[#3B82F6] outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-[#71717A] uppercase tracking-wider mb-1.5">Confirm New Password</label>
              <input
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                className="w-full bg-[#09090B] border border-[#27272A] rounded-xl px-4 py-3 text-white text-sm focus:border-[#3B82F6] outline-none transition-colors"
              />
            </div>
            {pwError && <p className="text-red-400 text-xs font-medium bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2">{pwError}</p>}
            {pwMsg && <p className="text-green-400 text-xs font-medium">{pwMsg}</p>}
            <button
              type="submit"
              disabled={pwSaving || !currentPw || !newPw || !confirmPw}
              className="px-5 py-2.5 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white text-sm font-bold rounded-xl transition-all disabled:opacity-50"
            >
              {pwSaving ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </section>
      )}

      {user?.google_user && (
        <section className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6">
          <h3 className="text-white font-bold text-lg mb-2">Password</h3>
          <p className="text-[#71717A] text-sm">You signed up with Google. Password management is handled by your Google account.</p>
        </section>
      )}

      {/* Social Media Connections */}
      <section>
        <SocialConnections />
      </section>

      {/* OAuth Test Console */}
      <section className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6 space-y-3">
        <h3 className="text-white font-bold text-lg">OAuth Test Console</h3>
        <p className="text-[#A1A1AA] text-sm">
          Open a dedicated page to test Facebook/Instagram and Twitter OAuth flows using backend credentials from <span className="text-[#E4E4E7] font-medium">backend/.env</span>.
        </p>
        <Link
          to="/oauth-test"
          className="inline-flex items-center px-5 py-2.5 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white text-sm font-bold rounded-xl transition-all"
        >
          Open OAuth Test Page →
        </Link>
      </section>

      {/* Danger Zone */}
      <section className="bg-[#18181B] border border-red-500/20 rounded-2xl p-6 space-y-4">
        <h3 className="text-red-400 font-bold text-lg">Danger Zone</h3>
        <p className="text-[#A1A1AA] text-sm">Permanently delete your account and all data. This cannot be undone.</p>

        <button
          onClick={() => setShowDeleteModal(true)}
          className="px-5 py-2.5 border border-red-500/40 text-red-400 hover:bg-red-500/10 text-sm font-bold rounded-xl transition-all"
        >
          Delete Account
        </button>
      </section>

      {/* Delete Account Modal */}
      {showDeleteModal && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => { setShowDeleteModal(false); setDeleteConfirmText(''); }}
        >
          <div
            className="bg-[#18181B] border border-red-500/30 rounded-2xl p-8 w-full max-w-md shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            <h3 className="text-red-400 font-bold text-xl mb-2">Delete Account</h3>
            <p className="text-[#A1A1AA] text-sm mb-6">This will permanently delete your account and all data. This cannot be undone.</p>
            <p className="text-red-300 text-sm font-semibold mb-2">Type <span className="font-black">DELETE</span> to confirm:</p>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="DELETE"
              autoFocus
              className="w-full bg-[#09090B] border border-red-500/30 rounded-xl px-4 py-3 text-white text-sm focus:border-red-500 outline-none transition-colors mb-5"
            />
            <div className="flex gap-3">
              <button
                onClick={handleDeleteAccount}
                disabled={deleteConfirmText !== 'DELETE' || deleting}
                className="flex-1 py-3 bg-red-600 hover:bg-red-500 text-white text-sm font-bold rounded-xl transition-all disabled:opacity-40"
              >
                {deleting ? 'Deleting...' : 'Confirm Delete'}
              </button>
              <button
                onClick={() => { setShowDeleteModal(false); setDeleteConfirmText(''); }}
                className="flex-1 py-3 bg-[#27272A] text-[#A1A1AA] hover:text-white text-sm font-bold rounded-xl transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
