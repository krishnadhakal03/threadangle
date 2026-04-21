import React, { useState, useEffect } from 'react';
import { useDialog } from '../context/DialogContext';
import { api } from '../utils/api';

// ─── Small helpers ──────────────────────────────────────────────────────────

const planBadge = (plan) => {
    const cls = plan === 'pro' || plan === 'founder' ? 'bg-amber-500/20 text-amber-500'
              : plan === 'starter' || plan === 'solo'  ? 'bg-blue-500/20 text-blue-500'
              : 'bg-gray-500/20 text-gray-500';
    return <span className={`px-2 py-1 rounded text-[10px] uppercase font-bold ${cls}`}>{plan}</span>;
};


const Admin = () => {
    const { alert: showAlert, confirm: confirmDialog } = useDialog();
    const [password, setPassword] = useState('');
    const [isAuthorized, setIsAuthorized] = useState(false);
    const [activeTab, setActiveTab] = useState('overview');
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [newsletterCount, setNewsletterCount] = useState(null);

    // CMS Content Management State
    const [cmsContent, setCmsContent] = useState([]);
    const [editingCms, setEditingCms] = useState(null);
    const [editingCmsValue, setEditingCmsValue] = useState('');
    const [cmsSaveLoading, setCmsSaveLoading] = useState(false);
    const [contentPageFilter, setContentPageFilter] = useState('');
    const [contentSectionFilter, setContentSectionFilter] = useState('all');
    const [contentSearch, setContentSearch] = useState('');
    const [settingsPageFilter, setSettingsPageFilter] = useState('');
    const [readerMode, setReaderMode] = useState(() => {
        try {
            const stored = localStorage.getItem('admin_reader_mode');
            return stored == null ? true : stored === 'true';
        } catch {
            return true;
        }
    });

    // Blog Management State
    const [blogPosts, setBlogPosts] = useState([]);
    const [isEditingPost, setIsEditingPost] = useState(false);
    const [currentPost, setCurrentPost] = useState(null);

    // User Management State
    const [users, setUsers] = useState([]);
    const [usersTotal, setUsersTotal] = useState(0);
    const [userSearch, setUserSearch] = useState('');
    const [usersLoading, setUsersLoading] = useState(false);
    const [editingUser, setEditingUser] = useState(null);
    const [userEdit, setUserEdit] = useState({});
    const [userSaveLoading, setUserSaveLoading] = useState(false);
    const [testEmail, setTestEmail] = useState('');
    const [sendingTestEmail, setSendingTestEmail] = useState(false);
    const [testEmailMessage, setTestEmailMessage] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const data = await api.getAdminStats(password);
            setStats(data);
            setIsAuthorized(true);
            fetchCmsContent();
            fetchBlogPosts();
            fetchUsers();
            try { const nc = await api.getNewsletterCount(password); setNewsletterCount(nc.count); } catch {}
        } catch (err) {
            setError('Invalid admin password');
        } finally {
            setLoading(false);
        }
    };

    const fetchCmsContent = async () => {
        try {
            const data = await api.getAllCMSAdmin(password);
            const flat = Array.isArray(data)
                ? data
                : Object.entries(data || {}).flatMap(([page, items]) =>
                    (Array.isArray(items) ? items : []).map(item => ({ ...item, page }))
                );
            setCmsContent(flat);
        } catch (err) {
            console.error('Failed to fetch CMS content');
        }
    };

    const fetchBlogPosts = async () => {
        try {
            const data = await api.getPosts();
            setBlogPosts(data);
        } catch (err) {
            console.error('Failed to fetch blog posts');
        }
    };

    const fetchUsers = async (search = '') => {
        setUsersLoading(true);
        try {
            const data = await api.getAdminUsers(password, search);
            setUsers(data.users);
            setUsersTotal(data.total);
        } catch (err) {
            console.error('Failed to fetch users');
        } finally {
            setUsersLoading(false);
        }
    };

    const handleUpdateCms = async (item) => {
        setCmsSaveLoading(true);
        try {
            // Use page + content_key (not item.id) — correct CMS PUT route
            await api.updateCMSContent(item.page, item.content_key, editingCmsValue, password);
            setEditingCms(null);
            setEditingCmsValue('');
            fetchCmsContent();
        } catch (err) {
            await showAlert({
                title: 'Update Failed',
                message: 'Failed to update content.',
                confirmText: 'OK',
                tone: 'danger',
            });
        } finally {
            setCmsSaveLoading(false);
        }
    };

    const handleToggleBooleanSetting = async (item) => {
        const toggled = String(item.content_value).toLowerCase() === 'true' ? 'false' : 'true';
        setCmsSaveLoading(true);
        try {
            await api.updateCMSContent(item.page, item.content_key, toggled, password);
            fetchCmsContent();
        } catch (err) {
            await showAlert({
                title: 'Update Failed',
                message: 'Failed to update setting.',
                confirmText: 'OK',
                tone: 'danger',
            });
        } finally {
            setCmsSaveLoading(false);
        }
    };

    const refreshStats = async () => {
        setLoading(true);
        try {
            const data = await api.getAdminStats(password);
            setStats(data);
            try { const nc = await api.getNewsletterCount(password); setNewsletterCount(nc.count); } catch {}
        } catch (err) {
            setError('Failed to refresh stats');
        } finally {
            setLoading(false);
        }
    };

    const handleSaveUser = async () => {
        setUserSaveLoading(true);
        try {
            const payload = {};
            if (userEdit.plan  !== undefined) payload.plan  = userEdit.plan;
            if (userEdit.usage_count !== undefined) payload.usage_count = Number(userEdit.usage_count);
            if (userEdit.custom_limit !== undefined) {
                payload.custom_limit = userEdit.custom_limit === '' ? -1 : Number(userEdit.custom_limit);
            }
            await api.updateAdminUser(editingUser.id, payload, password);
            setEditingUser(null);
            fetchUsers(userSearch);
        } catch (err) {
            await showAlert({
                title: 'User Update Failed',
                message: 'Failed to update user: ' + err.message,
                confirmText: 'OK',
                tone: 'danger',
            });
        } finally {
            setUserSaveLoading(false);
        }
    };

    const handleResetUsage = async (userId) => {
        const confirmed = await confirmDialog({
            title: 'Reset Usage?',
            message: 'Reset this user\'s usage count to 0?',
            confirmText: 'Reset Usage',
            cancelText: 'Cancel',
            tone: 'danger',
        });
        if (!confirmed) return;
        try {
            await api.resetUserUsage(userId, password);
            fetchUsers(userSearch);
        } catch (err) {
            await showAlert({
                title: 'Reset Failed',
                message: 'Failed to reset usage.',
                confirmText: 'OK',
                tone: 'danger',
            });
        }
    };

    const handleDeleteBlogPost = async (postId) => {
        const confirmed = await confirmDialog({
            title: 'Delete Post?',
            message: 'This will permanently delete the selected post.',
            confirmText: 'Delete Post',
            cancelText: 'Cancel',
            tone: 'danger',
        });
        if (!confirmed) return;

        try {
            await api.deleteBlogPost(postId, password);
            fetchBlogPosts();
        } catch {
            await showAlert({
                title: 'Delete Failed',
                message: 'Failed to delete post.',
                confirmText: 'OK',
                tone: 'danger',
            });
        }
    };

    const handleSaveBlogPost = async () => {
        try {
            if (currentPost.id) {
                await api.updateBlogPost(currentPost.id, currentPost, password);
            } else {
                await api.createBlogPost(currentPost, password);
            }
            setIsEditingPost(false);
            fetchBlogPosts();
        } catch (err) {
            await showAlert({
                title: 'Save Failed',
                message: 'Failed to save: ' + err.message,
                confirmText: 'OK',
                tone: 'danger',
            });
        }
    };

    const handleSendTestEmail = async () => {
        setSendingTestEmail(true);
        setTestEmailMessage('');
        try {
            const res = await api.sendAdminTestEmail(password, testEmail.trim());
            setTestEmailMessage(res.message || 'Test email sent');
        } catch (err) {
            setTestEmailMessage(err.message || 'Failed to send test email');
        } finally {
            setSendingTestEmail(false);
        }
    };

    // ── CMS page grouping ──────────────────────────────────────────────────
    const cmsPages = [...new Set(cmsContent.map(c => c.page).filter(Boolean))].sort();
    const settingsPages = ['settings', 'seo', 'email'].filter(page => cmsContent.some(c => c.page === page));

    useEffect(() => {
        if (!contentPageFilter && cmsPages.length > 0) {
            setContentPageFilter(cmsPages[0]);
        }
    }, [cmsPages, contentPageFilter]);

    useEffect(() => {
        if (!settingsPageFilter && settingsPages.length > 0) {
            setSettingsPageFilter(settingsPages[0]);
        }
    }, [settingsPages, settingsPageFilter]);

    useEffect(() => {
        try {
            localStorage.setItem('admin_reader_mode', String(readerMode));
        } catch {}
    }, [readerMode]);

    if (!isAuthorized) {
        return (
            <div className="min-h-screen bg-dark text-white flex items-center justify-center p-4">
                <div className="bg-card/50 backdrop-blur-xl border border-border rounded-2xl p-8 w-full max-w-sm shadow-2xl">
                    <h2 className="text-xl font-bold mb-6 text-center">Admin Access</h2>
                    <form onSubmit={handleLogin} className="space-y-4">
                        <input
                            type="password"
                            placeholder="Admin Password"
                            className="w-full bg-dark/60 border border-border rounded-xl p-4 text-white focus:border-accent outline-none"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                        {error && <p className="text-red-500 text-xs text-center">{error}</p>}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-accent hover:bg-accent/90 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-accent/20"
                        >
                            {loading ? 'Authorizing...' : 'Enter Dashboard'}
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    const TABS = ['overview', 'users', 'content', 'settings', 'blog'];

    return (
        <div className="min-h-screen bg-dark text-white p-8 font-sans">
            <div className="max-w-7xl mx-auto">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-6">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">Admin Panel</h1>
                        <p className="text-gray-500 text-sm font-medium mt-1">Manage content, users and growth</p>
                    </div>
                    <div className="flex flex-col items-stretch md:items-end gap-3 w-full md:w-auto">
                        <button
                            onClick={() => setReaderMode(prev => !prev)}
                            className={`self-start md:self-end px-4 py-2 rounded-xl text-[11px] font-semibold uppercase tracking-wide border transition-colors ${readerMode ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' : 'bg-card/40 text-gray-400 border-border hover:text-white'}`}
                        >
                            Reader Mode: {readerMode ? 'On' : 'Off'}
                        </button>
                        <div className="flex bg-card/50 border border-border p-1 rounded-2xl">
                            {TABS.map(tab => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-6 py-2.5 rounded-xl text-xs font-bold uppercase tracking-widest transition-all ${activeTab === tab ? 'bg-accent text-white shadow-lg' : 'text-gray-500 hover:text-white'}`}
                                >
                                    {tab}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* ── OVERVIEW TAB ───────────────────────────────────────────── */}
                {activeTab === 'overview' && stats && (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="flex justify-end mb-6">
                            <button onClick={refreshStats} disabled={loading} className="bg-card border border-border px-6 py-2 rounded-xl text-sm font-bold hover:border-accent/40 transition-all flex items-center gap-2">
                                {loading ? 'Refreshing...' : '🔄 Refresh Stats'}
                            </button>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
                            {[
                                { label: 'Total Users',       val: stats.overview.total_users,       sub: `+${stats.overview.users_today} today` },
                                { label: 'Total Generations', val: stats.overview.total_generations, sub: `+${stats.overview.generations_today} today` },
                                { label: 'Total Contacts',    val: stats.overview.total_contacts,    sub: `+${stats.overview.contacts_today} today` },
                                { label: 'Conversion', val: `${((stats.overview.starter_plan_users + stats.overview.pro_plan_users) / (stats.overview.total_users || 1) * 100).toFixed(1)}%`, sub: 'Paid users' }
                            ].map((c, i) => (
                                <div key={i} className="bg-card/30 border border-border/50 rounded-2xl p-6 shadow-lg">
                                    <p className="text-gray-500 text-xs font-bold uppercase tracking-wider mb-2">{c.label}</p>
                                    <p className="text-3xl font-bold mb-1">{c.val}</p>
                                    <p className="text-accent text-[11px] font-semibold">{c.sub}</p>
                                </div>
                            ))}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
                            {[
                                { label: 'Free Plan',     val: stats.overview.free_plan_users,    color: 'gray',  sub: 'Trial users' },
                                { label: 'Starter Plan',  val: stats.overview.starter_plan_users, color: 'blue',  sub: 'Active subscribers' },
                                { label: 'Pro Plan',      val: stats.overview.pro_plan_users,     color: 'amber', sub: 'Power users' },
                                { label: 'Newsletter',    val: newsletterCount ?? '—',            color: 'green', sub: 'Email subscribers' },
                            ].map((c, i) => (
                                <div key={i} className={`bg-gradient-to-br from-${c.color}-500/10 to-transparent border border-${c.color}-500/20 rounded-2xl p-6`}>
                                    <p className={`text-${c.color}-500 text-xs font-bold uppercase mb-4`}>{c.label}</p>
                                    <p className={`text-4xl font-bold text-${c.color}-400`}>{c.val}</p>
                                    <p className="text-sm text-gray-400 mt-2">{c.sub}</p>
                                </div>
                            ))}
                        </div>

                        <div className="grid lg:grid-cols-2 gap-8">
                            <div className="bg-card/40 border border-border rounded-2xl overflow-hidden shadow-xl">
                                <div className="px-6 py-4 border-b border-border bg-card/20">
                                    <h3 className="font-bold text-sm uppercase tracking-widest">Recent Users</h3>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-sm">
                                        <thead className="bg-dark/40 text-gray-500 font-bold uppercase text-[10px] tracking-widest">
                                            <tr><th className="px-6 py-3">User</th><th className="px-6 py-3">Plan</th><th className="px-6 py-3">Usage</th><th className="px-6 py-3">Joined</th></tr>
                                        </thead>
                                        <tbody className="divide-y divide-border/30">
                                            {stats.recent_users.map((u, i) => (
                                                <tr key={i} className="hover:bg-card/30 transition-colors">
                                                    <td className="px-6 py-4 font-medium">{u.email}</td>
                                                    <td className="px-6 py-4">{planBadge(u.plan)}</td>
                                                    <td className="px-6 py-4">{u.usage_count}</td>
                                                    <td className="px-6 py-4 text-gray-500">{new Date(u.created_at).toLocaleDateString()}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <div className="bg-card/40 border border-border rounded-2xl overflow-hidden shadow-xl">
                                <div className="px-6 py-4 border-b border-border bg-card/20">
                                    <h3 className="font-bold text-sm uppercase tracking-widest">Recent Generations</h3>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-sm">
                                        <thead className="bg-dark/40 text-gray-500 font-bold uppercase text-[10px] tracking-widest">
                                            <tr><th className="px-6 py-3">User</th><th className="px-6 py-3">Platforms</th><th className="px-6 py-3">Type</th><th className="px-6 py-3">Date</th></tr>
                                        </thead>
                                        <tbody className="divide-y divide-border/30">
                                            {stats.recent_generations.map((g, i) => (
                                                <tr key={i} className="hover:bg-card/30 transition-colors">
                                                    <td className="px-6 py-4 max-w-[150px] truncate">{g.user_email}</td>
                                                    <td className="px-6 py-4 text-[10px] font-bold text-accent uppercase">{g.platforms}</td>
                                                    <td className="px-6 py-4 capitalize">{g.input_type}</td>
                                                    <td className="px-6 py-4 text-gray-500">{new Date(g.created_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div className="mt-8 bg-card/40 border border-border rounded-2xl overflow-hidden shadow-xl">
                            <div className="px-6 py-4 border-b border-border bg-card/20">
                                <h3 className="font-bold text-sm uppercase tracking-widest">Recent Contacts</h3>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-dark/40 text-gray-500 font-bold uppercase text-[10px] tracking-widest">
                                        <tr><th className="px-6 py-3">Name</th><th className="px-6 py-3">Email</th><th className="px-6 py-3">Subject</th><th className="px-6 py-3">Date</th></tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/30">
                                        {stats.recent_contacts.map((c, i) => (
                                            <tr key={i} className="hover:bg-card/30 transition-colors">
                                                <td className="px-6 py-4 font-medium">{c.name}</td>
                                                <td className="px-6 py-4">{c.email}</td>
                                                <td className="px-6 py-4 text-gray-400">{c.subject}</td>
                                                <td className="px-6 py-4 text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── USERS TAB ──────────────────────────────────────────────── */}
                {activeTab === 'users' && (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
                        {/* Search + Refresh */}
                        <div className="flex gap-4 items-center">
                            <input
                                type="text"
                                placeholder="Search by email..."
                                value={userSearch}
                                onChange={(e) => setUserSearch(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && fetchUsers(userSearch)}
                                className={`flex-1 bg-dark/40 border border-border/70 rounded-xl px-4 ${readerMode ? 'py-3 text-sm text-gray-200' : 'py-2.5 text-xs text-gray-300'} focus:border-accent outline-none`}
                            />
                            <button onClick={() => fetchUsers(userSearch)} className="bg-accent text-white px-6 py-3 rounded-xl text-xs font-bold uppercase">
                                Search
                            </button>
                            <button onClick={() => { setUserSearch(''); fetchUsers(''); }} className="bg-card border border-border text-gray-400 px-6 py-3 rounded-xl text-xs font-bold uppercase hover:text-white transition-colors">
                                Clear
                            </button>
                        </div>

                        <p className={`${readerMode ? 'text-gray-400 text-sm' : 'text-gray-500 text-xs'} font-medium`}>{usersTotal} total users</p>

                        {/* User Edit Modal */}
                        {editingUser && (
                            <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                                <div className="bg-[#111113] border border-border rounded-2xl p-8 w-full max-w-lg shadow-2xl">
                                    <h3 className="text-lg font-bold mb-6">Edit User — <span className="text-accent font-mono text-sm">{editingUser.email}</span></h3>

                                    <div className="space-y-5">
                                        <div>
                                            <label className="block text-[11px] font-bold uppercase text-gray-500 mb-2">Plan</label>
                                            <select
                                                className="w-full bg-dark border border-border rounded-lg p-3 text-sm outline-none focus:border-accent"
                                                value={userEdit.plan ?? editingUser.plan}
                                                onChange={(e) => setUserEdit({...userEdit, plan: e.target.value})}
                                            >
                                                <option value="free">Free</option>
                                                <option value="solo">Starter (solo)</option>
                                                <option value="starter">Starter</option>
                                                <option value="founder">Pro (founder)</option>
                                                <option value="pro">Pro</option>
                                            </select>
                                        </div>

                                        <div>
                                            <label className="block text-[11px] font-bold uppercase text-gray-500 mb-2">
                                                Current Usage Count <span className="text-gray-600">(generations used this period)</span>
                                            </label>
                                            <input
                                                type="number"
                                                min="0"
                                                className="w-full bg-dark border border-border rounded-lg p-3 text-sm outline-none focus:border-accent"
                                                value={userEdit.usage_count ?? editingUser.usage_count}
                                                onChange={(e) => setUserEdit({...userEdit, usage_count: e.target.value})}
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-[11px] font-bold uppercase text-gray-500 mb-2">
                                                Custom Limit Override <span className="text-gray-600">(leave blank for plan default · -1 to clear)</span>
                                            </label>
                                            <input
                                                type="number"
                                                placeholder={`Plan default: ${editingUser.plan_default_limit ?? 'Unlimited'}`}
                                                className="w-full bg-dark border border-border rounded-lg p-3 text-sm outline-none focus:border-accent"
                                                value={userEdit.custom_limit ?? (editingUser.custom_limit != null ? editingUser.custom_limit : '')}
                                                onChange={(e) => setUserEdit({...userEdit, custom_limit: e.target.value})}
                                            />
                                            <p className="text-[11px] text-gray-600 mt-1">
                                                Currently: {editingUser.custom_limit != null ? `Custom limit: ${editingUser.custom_limit}` : 'Using plan default'}
                                            </p>
                                        </div>

                                        <div className="flex gap-3 pt-2">
                                            <button
                                                onClick={handleSaveUser}
                                                disabled={userSaveLoading}
                                                className="flex-1 bg-accent text-white py-3 rounded-xl font-bold text-xs uppercase shadow-lg shadow-accent/20"
                                            >
                                                {userSaveLoading ? 'Saving...' : '💾 Save Changes'}
                                            </button>
                                            <button
                                                onClick={() => handleResetUsage(editingUser.id)}
                                                className="bg-orange-500/10 border border-orange-500/30 text-orange-400 px-4 py-3 rounded-xl text-xs font-bold uppercase hover:bg-orange-500/20 transition-colors"
                                            >
                                                Reset Usage
                                            </button>
                                            <button
                                                onClick={() => { setEditingUser(null); setUserEdit({}); }}
                                                className="bg-dark border border-border text-gray-400 px-4 py-3 rounded-xl text-xs font-bold uppercase hover:text-white"
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Users Table */}
                        <div className={`${readerMode ? 'bg-card/20 border-border/40' : 'bg-card/30 border-border/50'} border rounded-2xl overflow-hidden shadow-xl`}>
                            <div className="overflow-x-auto">
                                <table className={`w-full text-left ${readerMode ? 'text-sm' : 'text-xs'}`}>
                                    <thead className={`bg-dark/40 ${readerMode ? 'text-gray-400 text-[11px] tracking-wide' : 'text-gray-500 text-[10px] tracking-widest'} font-bold uppercase`}>
                                        <tr>
                                            <th className={`px-6 ${readerMode ? 'py-3.5' : 'py-3'}`}>Email</th>
                                            <th className={`px-6 ${readerMode ? 'py-3.5' : 'py-3'}`}>Plan</th>
                                            <th className={`px-6 ${readerMode ? 'py-3.5' : 'py-3'}`}>Usage</th>
                                            <th className={`px-6 ${readerMode ? 'py-3.5' : 'py-3'}`}>Limit</th>
                                            <th className={`px-6 ${readerMode ? 'py-3.5' : 'py-3'}`}>Custom</th>
                                            <th className={`px-6 ${readerMode ? 'py-3.5' : 'py-3'}`}>Joined</th>
                                            <th className={`px-6 ${readerMode ? 'py-3.5' : 'py-3'} text-right`}>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/30">
                                        {usersLoading ? (
                                            <tr><td colSpan="7" className="px-6 py-8 text-center text-gray-500">Loading users...</td></tr>
                                        ) : users.map((u) => (
                                            <tr key={u.id} className="hover:bg-card/10 transition-colors">
                                                <td className={`px-6 ${readerMode ? 'py-4.5' : 'py-4'}`}>
                                                    <div className="font-medium">{u.email}</div>
                                                    {u.name && <div className="text-xs text-gray-500">{u.name}</div>}
                                                </td>
                                                <td className={`px-6 ${readerMode ? 'py-4.5' : 'py-4'}`}>{planBadge(u.plan)}</td>
                                                <td className={`px-6 ${readerMode ? 'py-4.5' : 'py-4'} font-mono text-gray-200`}>{u.usage_count}</td>
                                                <td className={`px-6 ${readerMode ? 'py-4.5' : 'py-4'} text-gray-300 font-mono`}>
                                                    {u.custom_limit != null ? (
                                                        <span className="text-amber-400">{u.custom_limit}</span>
                                                    ) : (
                                                        <span>{u.plan_default_limit ?? '∞'}</span>
                                                    )}
                                                </td>
                                                <td className={`px-6 ${readerMode ? 'py-4.5 text-xs' : 'py-4 text-[10px]'}`}>
                                                    {u.custom_limit != null ? (
                                                        <span className="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded font-bold">CUSTOM</span>
                                                    ) : (
                                                        <span className="text-gray-600">—</span>
                                                    )}
                                                </td>
                                                <td className={`px-6 ${readerMode ? 'py-4.5' : 'py-4'} text-gray-400`}>{new Date(u.created_at).toLocaleDateString()}</td>
                                                <td className={`px-6 ${readerMode ? 'py-4.5' : 'py-4'} text-right space-x-3`}>
                                                    <button
                                                        onClick={() => { setEditingUser(u); setUserEdit({}); }}
                                                        className="text-accent hover:underline text-xs font-semibold uppercase"
                                                    >
                                                        Edit
                                                    </button>
                                                    <button
                                                        onClick={() => handleResetUsage(u.id)}
                                                        className="text-orange-400 hover:underline text-xs font-semibold uppercase"
                                                    >
                                                        Reset
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── CONTENT TAB ────────────────────────────────────────────── */}
                {activeTab === 'content' && (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
                        {cmsContent.length === 0 ? (
                            <div className="text-center py-20 text-gray-500">
                                <p className="text-2xl mb-4">No CMS content found</p>
                                <p className="text-sm">Run <code className="bg-card px-2 py-1 rounded">python seed_cms.py</code> in the backend folder to populate content.</p>
                            </div>
                        ) : (
                            <>
                                <div className={`${readerMode ? 'bg-card/20 border-border/40 p-5' : 'bg-card/30 border-border/50 p-4'} border rounded-2xl space-y-4`}>
                                    <div className="flex flex-wrap gap-2">
                                        {cmsPages.map((page, idx) => (
                                            <button
                                                key={`${page}-${idx}`}
                                                onClick={() => {
                                                    setContentPageFilter(page);
                                                    setContentSectionFilter('all');
                                                }}
                                                className={`px-4 py-2 rounded-lg ${readerMode ? 'text-sm font-medium' : 'text-xs font-semibold uppercase tracking-wide'} capitalize border transition-colors ${contentPageFilter === page ? 'bg-accent/90 text-white border-accent' : 'bg-dark/40 text-gray-300 border-border/70 hover:text-gray-100 hover:bg-dark/60'}`}
                                            >
                                                {page}
                                            </button>
                                        ))}
                                    </div>

                                    <div className="flex flex-col md:flex-row gap-3">
                                        <input
                                            type="text"
                                            placeholder="Search by label or key..."
                                            value={contentSearch}
                                            onChange={(e) => setContentSearch(e.target.value)}
                                            className={`flex-1 bg-dark/40 border border-border/70 rounded-xl px-4 ${readerMode ? 'py-3 text-sm' : 'py-2.5 text-xs'} text-gray-200 placeholder:text-gray-500 focus:border-accent outline-none`}
                                        />
                                        <select
                                            value={contentSectionFilter}
                                            onChange={(e) => setContentSectionFilter(e.target.value)}
                                            className={`bg-dark/40 border border-border/70 rounded-xl px-4 ${readerMode ? 'py-3 text-sm' : 'py-2.5 text-xs'} text-gray-200 focus:border-accent outline-none`}
                                        >
                                            <option value="all">All Sections</option>
                                            {[...new Set(cmsContent.filter(c => c.page === contentPageFilter).map(c => c.section).filter(Boolean))]
                                                .sort()
                                                .map((section) => (
                                                    <option key={section} value={section}>{section}</option>
                                                ))}
                                        </select>
                                    </div>
                                </div>

                                <div className={`${readerMode ? 'bg-card/20 border-border/40' : 'bg-card/30 border-border/50'} border rounded-[2rem] overflow-hidden`}>
                                    <div className="px-8 py-6 border-b border-border/10 bg-card/10 flex justify-between items-center">
                                        <h3 className="text-xl font-semibold text-gray-100 capitalize">{contentPageFilter || 'Content'} Page</h3>
                                        <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                                            {
                                                cmsContent
                                                    .filter(c => c.page === contentPageFilter)
                                                    .filter(c => contentSectionFilter === 'all' ? true : c.section === contentSectionFilter)
                                                    .filter(c => {
                                                        if (!contentSearch.trim()) return true;
                                                        const q = contentSearch.toLowerCase();
                                                        return (c.label || '').toLowerCase().includes(q) || (c.content_key || '').toLowerCase().includes(q);
                                                    }).length
                                            } Fields
                                        </span>
                                    </div>
                                    <div className="divide-y divide-border/10">
                                        {cmsContent
                                            .filter(c => c.page === contentPageFilter)
                                            .filter(c => contentSectionFilter === 'all' ? true : c.section === contentSectionFilter)
                                            .filter(c => {
                                                if (!contentSearch.trim()) return true;
                                                const q = contentSearch.toLowerCase();
                                                return (c.label || '').toLowerCase().includes(q) || (c.content_key || '').toLowerCase().includes(q);
                                            })
                                            .map(item => (
                                                <div key={item.id || item.content_key} className={`${readerMode ? 'p-6' : 'p-5'} hover:bg-card/10 transition-colors`}>
                                                    <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-center gap-3 mb-3 flex-wrap">
                                                                <span className={`${readerMode ? 'text-sm' : 'text-xs uppercase tracking-wide'} font-medium text-gray-100`}>{item.label}</span>
                                                                <span className="text-xs text-gray-500 font-mono">{item.content_key}</span>
                                                                {item.section && <span className="text-xs text-gray-400 capitalize">{item.section}</span>}
                                                                <span className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded ${
                                                                    item.content_type === 'json' ? 'bg-purple-500/20 text-purple-400' :
                                                                    item.content_type === 'url'  ? 'bg-blue-500/20 text-blue-400' :
                                                                    item.content_type === 'boolean' ? 'bg-green-500/20 text-green-400' :
                                                                    item.content_type === 'integer' ? 'bg-amber-500/20 text-amber-400' :
                                                                    'bg-gray-500/20 text-gray-400'
                                                                }`}>{item.content_type}</span>
                                                            </div>
                                                            {editingCms === item.id ? (
                                                                <div className="space-y-4">
                                                                    <textarea
                                                                        className={`w-full bg-dark/40 border border-border/70 rounded-xl p-4 text-gray-200 focus:border-accent outline-none text-sm leading-relaxed ${item.content_type === 'json' ? 'font-mono' : 'font-sans'}`}
                                                                        style={{ minHeight: item.content_type === 'json' ? '200px' : item.content_type === 'textarea' ? '120px' : '56px', resize: 'vertical' }}
                                                                        value={editingCmsValue}
                                                                        onChange={(e) => setEditingCmsValue(e.target.value)}
                                                                    />
                                                                    {item.content_type === 'json' && (
                                                                        <p className="text-xs text-gray-400">Edit raw JSON. Make sure it is valid before saving.</p>
                                                                    )}
                                                                    <div className="flex gap-3">
                                                                        <button
                                                                            onClick={() => handleUpdateCms(item)}
                                                                            disabled={cmsSaveLoading}
                                                                            className="bg-accent text-white px-6 py-2 rounded-xl text-xs font-bold uppercase shadow-lg shadow-accent/20"
                                                                        >
                                                                            {cmsSaveLoading ? 'Saving...' : '💾 Save'}
                                                                        </button>
                                                                        <button
                                                                            onClick={() => { setEditingCms(null); setEditingCmsValue(''); }}
                                                                            className="bg-dark border border-border text-gray-400 px-6 py-2 rounded-xl text-xs font-bold uppercase"
                                                                        >
                                                                            Cancel
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            ) : (
                                                                <p className={`${readerMode ? 'text-gray-300 text-[15px] leading-7 line-clamp-4' : 'text-gray-200 text-sm leading-6 line-clamp-3'} whitespace-pre-wrap break-words`}>
                                                                    {item.content_value}
                                                                </p>
                                                            )}
                                                        </div>
                                                        {editingCms !== item.id && (
                                                            <button
                                                                onClick={() => { setEditingCms(item.id); setEditingCmsValue(item.content_value); }}
                                                                className="text-xs font-medium text-accent hover:underline uppercase tracking-wide whitespace-nowrap flex-shrink-0"
                                                            >
                                                                Edit
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        {cmsContent
                                            .filter(c => c.page === contentPageFilter)
                                            .filter(c => contentSectionFilter === 'all' ? true : c.section === contentSectionFilter)
                                            .filter(c => {
                                                if (!contentSearch.trim()) return true;
                                                const q = contentSearch.toLowerCase();
                                                return (c.label || '').toLowerCase().includes(q) || (c.content_key || '').toLowerCase().includes(q);
                                            }).length === 0 && (
                                            <div className="p-8 text-center text-gray-400 text-sm">
                                                No content matches this filter.
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ── BLOG TAB ───────────────────────────────────────────────── */}
                {activeTab === 'settings' && (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
                        <div className={`${readerMode ? 'bg-card/20 border-border/40' : 'bg-card/30 border-border/50'} border rounded-2xl p-6`}>
                            <h3 className="text-lg font-bold mb-2">Email Template Test</h3>
                            <p className="text-sm text-gray-400 mb-4">Send a branded test email using current CMS email settings.</p>
                            <div className="flex flex-col md:flex-row gap-3">
                                <input
                                    type="email"
                                    placeholder="Recipient email (leave blank to use ZOHO_EMAIL)"
                                    className={`flex-1 bg-dark/40 border border-border/70 rounded-xl px-4 ${readerMode ? 'py-3 text-sm' : 'py-2.5 text-xs'} text-gray-200 placeholder:text-gray-500 focus:border-accent outline-none`}
                                    value={testEmail}
                                    onChange={(e) => setTestEmail(e.target.value)}
                                />
                                <button
                                    onClick={handleSendTestEmail}
                                    disabled={sendingTestEmail}
                                    className="bg-accent text-white px-6 py-3 rounded-xl text-xs font-bold uppercase shadow-lg shadow-accent/20"
                                >
                                    {sendingTestEmail ? 'Sending...' : 'Send Test Email'}
                                </button>
                            </div>
                            {testEmailMessage && (
                                <p className="text-sm mt-3 text-gray-300">{testEmailMessage}</p>
                            )}
                        </div>

                        <div className={`${readerMode ? 'bg-card/20 border-border/40' : 'bg-card/30 border-border/50'} border rounded-2xl p-4 space-y-4`}>
                            <div className="flex flex-wrap gap-2">
                                {settingsPages.map(page => (
                                    <button
                                        key={page}
                                        onClick={() => setSettingsPageFilter(page)}
                                        className={`px-4 py-2 rounded-lg ${readerMode ? 'text-sm font-medium' : 'text-xs font-semibold uppercase tracking-wide'} capitalize border transition-colors ${settingsPageFilter === page ? 'bg-accent/90 text-white border-accent' : 'bg-dark/40 text-gray-300 border-border/70 hover:text-gray-100 hover:bg-dark/60'}`}
                                    >
                                        {page}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {settingsPages.map(page => {
                            if (settingsPageFilter !== page) return null;
                            const pageItems = cmsContent.filter(c => c.page === page);
                            if (pageItems.length === 0) return null;
                            return (
                                <div key={page} className={`${readerMode ? 'bg-card/20 border-border/40' : 'bg-card/30 border-border/50'} border rounded-[2rem] overflow-hidden`}>
                                    <div className="px-8 py-6 border-b border-border/10 bg-card/10 flex justify-between items-center">
                                        <h3 className="text-xl font-semibold text-gray-100 capitalize">{page} Settings</h3>
                                        <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">{pageItems.length} Fields</span>
                                    </div>
                                    <div className="divide-y divide-border/10">
                                        {pageItems.map(item => (
                                            <div key={item.id || item.content_key} className={`${readerMode ? 'p-6' : 'p-5'} hover:bg-card/10 transition-colors`}>
                                                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center gap-3 mb-3 flex-wrap">
                                                            <span className={`${readerMode ? 'text-sm' : 'text-xs uppercase tracking-wide'} font-medium text-gray-100`}>{item.label}</span>
                                                            <span className="text-xs text-gray-500 font-mono">{item.content_key}</span>
                                                            <span className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded ${
                                                                item.content_type === 'json' ? 'bg-purple-500/20 text-purple-400' :
                                                                item.content_type === 'url'  ? 'bg-blue-500/20 text-blue-400' :
                                                                item.content_type === 'boolean' ? 'bg-green-500/20 text-green-400' :
                                                                item.content_type === 'integer' ? 'bg-amber-500/20 text-amber-400' :
                                                                'bg-gray-500/20 text-gray-400'
                                                            }`}>{item.content_type}</span>
                                                        </div>

                                                        {editingCms === item.id ? (
                                                            <div className="space-y-4">
                                                                <textarea
                                                                    className={`w-full bg-dark/40 border border-border/70 rounded-xl p-4 text-gray-200 focus:border-accent outline-none ${readerMode ? 'text-sm leading-relaxed' : 'text-xs leading-6'} ${item.content_type === 'json' ? 'font-mono' : 'font-sans'}`}
                                                                    style={{ minHeight: item.content_type === 'json' ? '180px' : '64px', resize: 'vertical' }}
                                                                    value={editingCmsValue}
                                                                    onChange={(e) => setEditingCmsValue(e.target.value)}
                                                                />
                                                                <div className="flex gap-3">
                                                                    <button onClick={() => handleUpdateCms(item)} disabled={cmsSaveLoading} className="bg-accent text-white px-6 py-2 rounded-xl text-xs font-bold uppercase shadow-lg shadow-accent/20">
                                                                        {cmsSaveLoading ? 'Saving...' : '💾 Save'}
                                                                    </button>
                                                                    <button onClick={() => { setEditingCms(null); setEditingCmsValue(''); }} className="bg-dark border border-border text-gray-400 px-6 py-2 rounded-xl text-xs font-bold uppercase">
                                                                        Cancel
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        ) : (
                                                            <p className={`${readerMode ? 'text-gray-300 text-[15px] leading-7' : 'text-gray-200 text-sm leading-6'} whitespace-pre-wrap break-words`}>{item.content_value}</p>
                                                        )}
                                                    </div>

                                                    <div className="flex items-center gap-2">
                                                        {item.content_type === 'boolean' ? (
                                                            <button
                                                                onClick={() => handleToggleBooleanSetting(item)}
                                                                className={`px-4 py-2 rounded-lg text-xs font-bold uppercase ${String(item.content_value).toLowerCase() === 'true' ? 'bg-green-500/20 text-green-400 border border-green-500/40' : 'bg-gray-500/20 text-gray-400 border border-gray-500/40'}`}
                                                            >
                                                                {String(item.content_value).toLowerCase() === 'true' ? 'Enabled' : 'Disabled'}
                                                            </button>
                                                        ) : null}
                                                        {editingCms !== item.id && (
                                                            <button
                                                                onClick={() => { setEditingCms(item.id); setEditingCmsValue(item.content_value); }}
                                                                className="text-xs font-bold text-accent hover:underline uppercase tracking-widest whitespace-nowrap"
                                                            >
                                                                Edit
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* ── BLOG TAB ───────────────────────────────────────────────── */}
                {activeTab === 'blog' && (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {!isEditingPost ? (
                            <div className={`${readerMode ? 'bg-card/20 border-border/40' : 'bg-card/30 border-border/50'} border rounded-2xl overflow-hidden shadow-xl`}>
                                <div className="px-8 py-6 border-b border-border/10 bg-card/10 flex justify-between items-center">
                                    <h3 className="font-bold">Blog Management</h3>
                                    <button
                                        onClick={() => {
                                            setCurrentPost({ title: '', slug: '', content: '', category: 'Social Media Strategy', author: 'Threadangle Team', cover_image: '', tags: [] });
                                            setIsEditingPost(true);
                                        }}
                                        className="bg-accent text-white px-6 py-2 rounded-xl text-xs font-bold uppercase shadow-lg shadow-accent/20"
                                    >
                                        + Create New Post
                                    </button>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className={`w-full text-left ${readerMode ? 'text-sm' : 'text-xs'}`}>
                                        <thead className={`bg-dark/40 ${readerMode ? 'text-gray-400 text-[11px] tracking-wide' : 'text-gray-500 text-[10px] tracking-widest'} font-bold uppercase`}>
                                            <tr><th className={`px-8 ${readerMode ? 'py-4.5' : 'py-4'}`}>Title</th><th className={`px-8 ${readerMode ? 'py-4.5' : 'py-4'}`}>Category</th><th className={`px-8 ${readerMode ? 'py-4.5' : 'py-4'}`}>Author</th><th className={`px-8 ${readerMode ? 'py-4.5' : 'py-4'}`}>Stats</th><th className={`px-8 ${readerMode ? 'py-4.5' : 'py-4'}`}>Status</th><th className={`px-8 ${readerMode ? 'py-4.5' : 'py-4'} text-right`}>Actions</th></tr>
                                        </thead>
                                        <tbody className="divide-y divide-border/30">
                                            {blogPosts.map((post) => (
                                                <tr key={post.id} className="hover:bg-card/10 transition-colors">
                                                    <td className={`px-8 ${readerMode ? 'py-5' : 'py-4.5'}`}>
                                                        <div className={`${readerMode ? 'text-base' : 'text-sm'} font-semibold text-gray-100 mb-1`}>{post.title}</div>
                                                        <div className={`${readerMode ? 'text-xs' : 'text-[10px]'} text-gray-500 font-medium truncate max-w-[240px]`}>{post.slug}</div>
                                                    </td>
                                                    <td className={`px-8 ${readerMode ? 'py-5' : 'py-4.5'}`}><span className="bg-card border border-border px-3 py-1 rounded-full text-[10px] uppercase font-bold text-gray-400">{post.category}</span></td>
                                                    <td className={`px-8 ${readerMode ? 'py-5' : 'py-4.5'} text-gray-300`}>{post.author}</td>
                                                    <td className={`px-8 ${readerMode ? 'py-5' : 'py-4.5'}`}>
                                                        <div className="flex gap-4">
                                                            <div className="text-center"><div className="text-[10px] font-bold text-gray-600 uppercase">Views</div><div className="font-bold">{post.views || 0}</div></div>
                                                            <div className="text-center"><div className="text-[10px] font-bold text-gray-600 uppercase">Time</div><div className="font-bold">{post.read_time_minutes || 0}m</div></div>
                                                        </div>
                                                    </td>
                                                    <td className={`px-8 ${readerMode ? 'py-5' : 'py-4.5'}`}><span className="text-green-500 text-[10px] font-bold uppercase tracking-widest">● Published</span></td>
                                                    <td className={`px-8 ${readerMode ? 'py-5' : 'py-4.5'} text-right space-x-4`}>
                                                        <button onClick={() => { setCurrentPost({...post}); setIsEditingPost(true); }} className="text-accent hover:underline text-xs font-semibold uppercase tracking-wide">Edit</button>
                                                        <button onClick={() => handleDeleteBlogPost(post.id)} className="text-red-500 hover:underline text-xs font-semibold uppercase tracking-wide">Delete</button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-card/40 border border-border rounded-[2.5rem] p-10 shadow-2xl animate-in zoom-in-95 duration-300">
                                <div className="flex justify-between items-center mb-10 pb-6 border-b border-border/10">
                                    <h3 className="text-2xl font-bold">{currentPost.id ? 'Edit Post' : 'New Publication'}</h3>
                                    <button onClick={() => setIsEditingPost(false)} className="text-gray-500 hover:text-white">✕ Close Editor</button>
                                </div>
                                <div className="grid lg:grid-cols-3 gap-10">
                                    <div className="lg:col-span-2 space-y-8">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black uppercase text-gray-500">Title</label>
                                            <input
                                                className="w-full bg-dark/60 border border-border rounded-xl p-6 text-xl font-bold text-white focus:border-accent outline-none"
                                                value={currentPost.title}
                                                onChange={(e) => { const title = e.target.value; const slug = title.toLowerCase().replace(/ /g, '-').replace(/[^\w-]+/g, ''); setCurrentPost({...currentPost, title, slug}); }}
                                                placeholder="Enter a viral title..."
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black uppercase text-gray-500">Article Content (Markdown)</label>
                                            <textarea
                                                className="w-full bg-dark/60 border border-border rounded-2xl p-6 text-white text-sm leading-relaxed focus:border-accent outline-none min-h-[500px] font-mono"
                                                value={currentPost.content}
                                                onChange={(e) => setCurrentPost({...currentPost, content: e.target.value})}
                                                placeholder="Write your story here..."
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-8">
                                        <div className="bg-dark/40 border border-border rounded-2xl p-6 space-y-6">
                                            <h4 className="text-xs font-bold uppercase text-accent tracking-widest">Publishing Details</h4>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-bold uppercase text-gray-600">Permalink</label>
                                                <div className="flex items-center gap-2 text-[11px] text-gray-500 bg-black/20 p-3 rounded-lg border border-border/10">/blog/{currentPost.slug}</div>
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-bold uppercase text-gray-600">Category</label>
                                                <select className="w-full bg-dark border border-border rounded-lg p-3 text-xs font-bold outline-none focus:border-accent" value={currentPost.category} onChange={(e) => setCurrentPost({...currentPost, category: e.target.value})}>
                                                    <option>Social Media Strategy</option>
                                                    <option>Productivity</option>
                                                    <option>Growth Hacks</option>
                                                    <option>AI & Tech</option>
                                                </select>
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-bold uppercase text-gray-600">Featured Image URL</label>
                                                <input className="w-full bg-dark border border-border rounded-lg p-3 text-xs outline-none focus:border-accent" value={currentPost.cover_image || ''} onChange={(e) => setCurrentPost({...currentPost, cover_image: e.target.value})} />
                                                {currentPost.cover_image && <img src={currentPost.cover_image} className="w-full h-32 object-cover rounded-lg mt-2 opacity-50 border border-border/20" alt="Preview" onError={(e) => e.target.style.display='none'} />}
                                            </div>
                                            <div className="pt-6 border-t border-border/10 flex flex-col gap-3">
                                                <button onClick={handleSaveBlogPost} className="w-full bg-accent text-white py-3 rounded-xl font-bold text-xs uppercase shadow-xl shadow-accent/20">
                                                    {currentPost.id ? 'Update Publication' : 'Publish Article'}
                                                </button>
                                                <button onClick={() => setIsEditingPost(false)} className="w-full bg-card border border-border py-3 rounded-xl font-bold text-xs uppercase text-gray-400 hover:text-white">Discard</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Admin;
