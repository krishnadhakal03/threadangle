const API_URL = (import.meta.env.VITE_API_URL || '') + '/api';

let token = null;

const parseResponseBody = async (response) => {
    const raw = await response.text();
    if (!raw) return null;

    try {
        return JSON.parse(raw);
    } catch {
        return raw;
    }
};

export const setAuthToken = (newToken) => {
    token = newToken;
};

export const request = async (path, options = {}) => {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        // Handle unauthorized (redirect or clear session)
        window.dispatchEvent(new CustomEvent('auth-unauthorized'));
    }

    const data = await parseResponseBody(response);
    if (!response.ok) {
        const message = typeof data === 'string'
            ? data
            : (typeof data?.detail === 'object' ? data.detail?.message : data?.detail) || response.statusText || 'Something went wrong';
        const err = new Error(message);
        err.status = response.status;
        err.detail = typeof data === 'object' && data !== null ? data.detail : data;
        throw err;
    }

    return data;
};

export const api = {
    signup: (email, password) => request('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    }),
    login: (email, password) => request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    }),
    getMe: () => request('/auth/me'),
    getHistory: () => request('/generate/history'),
    createCheckout: (plan) => request(`/payments/create-checkout?plan=${plan}`, { method: 'POST' }),
    verifySession: (sessionId) => request(`/payments/verify-session?session_id=${sessionId}`, { method: 'POST' }),
    getPortal: () => request('/payments/portal', { method: 'POST' }),
    generate: (payload) => request('/generate/', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    generateFreeVideo: (payload) => request('/generate/video/free', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    generateVideoPlan: (payload) => request('/generate/video/plan', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    getVideoMode: () => request('/generate/video/mode'),
    generateVideoPreview: (payload) => request('/generate/video/preview', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    generateVideoFromPreview: (payload) => request('/generate/video/generate-from-preview', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    regenerateSceneImage: (payload) => request('/generate/regenerate-scene-image', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    generateSportsMotionPreview: (payload) => request('/generate/sports/motion-preview', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    createSportsFinalStitch: async (formData) => {
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}/generate/sports/final-stitch`, {
            method: 'POST',
            headers,
            body: formData,
        });

        const data = await parseResponseBody(response);
        if (!response.ok) {
            const message = typeof data === 'string'
                ? data
                : (typeof data?.detail === 'object' ? data.detail?.message : data?.detail) || response.statusText || 'Something went wrong';
            const err = new Error(message);
            err.status = response.status;
            err.detail = typeof data === 'object' && data !== null ? data.detail : data;
            throw err;
        }
        return data;
    },
    getCharacterPresets: () => request('/generate/video/characters/presets'),
    regenerateThumbnail: (payload) => request('/generate/regenerate-thumbnail', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    saveVideoEditorChanges: (payload) => request('/generate/video/editor/save', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    getVideoAnalytics: () => request('/generate/analytics'),
    getApiCredits: () => request('/generate/video/credits'),
    generateVideoBatch: (payload) => request('/generate/video/batch', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    getVideoBatchStatus: (batchId) => request(`/generate/video/batch/${encodeURIComponent(batchId)}`),
    getVideoHistory: () => request('/generate/video/history'),
    getVideoHistoryItem: (generationId) => request(`/generate/video/history/${encodeURIComponent(generationId)}`),
    deleteVideoHistoryItem: async (generationId) => {
        const encoded = encodeURIComponent(generationId);
        try {
            return await request(`/generate/video/${encoded}`, { method: 'DELETE' });
        } catch (err) {
            if (err?.status === 404) {
                return request(`/generate/video/history/${encoded}`, { method: 'DELETE' });
            }
            throw err;
        }
    },
    getVideoProgress: (generationId) => request(`/generate/video/progress/${encodeURIComponent(generationId)}`),
    getVideoDownloadUrl: (filename) => `${API_URL}/generate/video/download/${encodeURIComponent(filename)}`,
    fetchVideoBlob: async (downloadPath) => {
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const base = import.meta.env.VITE_API_URL || '';
        const url = (downloadPath || '').startsWith('http') ? downloadPath : `${base}${downloadPath}`;

        const response = await fetch(url, { headers });
        if (!response.ok) {
            let message = 'Unable to fetch video file';
            try {
                const data = await response.json();
                message = (typeof data.detail === 'object' ? data.detail?.message : data.detail) || message;
            } catch {
                // ignore json parsing errors
            }
            throw new Error(message);
        }

        const blob = await response.blob();
        return { blobUrl: URL.createObjectURL(blob) };
    },
    saveEdit: (generationId, platform, editedContent) => request(`/generate/${generationId}/edit`, {
        method: 'PUT',
        body: JSON.stringify({ platform, edited_content: editedContent }),
    }),
    completeOnboarding: () => request('/auth/onboarding-complete', { method: 'PATCH' }),
    updateName: (name) => request('/auth/update-name', {
        method: 'PUT',
        body: JSON.stringify({ name }),
    }),
    changePassword: (current_password, new_password) => request('/auth/change-password', {
        method: 'PUT',
        body: JSON.stringify({ current_password, new_password }),
    }),
    deleteAccount: () => request('/auth/delete-account', { method: 'DELETE' }),
    forgotPassword: (email) => request('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email }),
    }),
    verifyResetToken: (token) => request(`/auth/verify-reset-token?token=${token}`),
    resetPassword: (token, newPassword) => request('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ token, new_password: newPassword }),
    }),
    submitContact: (payload) => request('/contact', {
        method: 'POST',
        body: JSON.stringify(payload),
    }),
    
    // CMS
    getCMSContent: (page) => request(`/cms/${page}`),
    updateCMSContent: (page, key, value, adminPassword) => request(`/cms/${page}/${key}`, {
        method: 'PUT',
        body: JSON.stringify({ content_value: value }),
        headers: { 'X-Admin-Password': adminPassword }
    }),
    getAllCMSAdmin: (adminPassword) => request('/cms/admin/all', {
        headers: { 'X-Admin-Password': adminPassword }
    }),

    // Blog
    getPosts: (category = null, tag = null, limit = 10, offset = 0) => {
        let url = `/blog/posts?limit=${limit}&offset=${offset}`;
        if (category) url += `&category=${encodeURIComponent(category)}`;
        if (tag) url += `&tag=${encodeURIComponent(tag)}`;
        return request(url);
    },
    getPost: (slug) => request(`/blog/posts/${slug}`),
    getRelatedPosts: (slug) => request(`/blog/posts/${slug}/related`),
    getCategories: () => request('/blog/categories'),
    getFeaturedPosts: () => request('/blog/featured'),

    // Admin
    getAdminStats: (adminPassword) => request('/admin/stats', {
        headers: { 'X-Admin-Password': adminPassword }
    }),
    getAdminUsers: (adminPassword, search = '', limit = 100, offset = 0) => request(
        `/admin/users?limit=${limit}&offset=${offset}${search ? `&search=${encodeURIComponent(search)}` : ''}`,
        { headers: { 'X-Admin-Password': adminPassword } }
    ),
    updateAdminUser: (userId, data, adminPassword) => request(`/admin/users/${userId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
        headers: { 'X-Admin-Password': adminPassword }
    }),
    resetUserUsage: (userId, adminPassword) => request(`/admin/users/${userId}/reset-usage`, {
        method: 'POST',
        headers: { 'X-Admin-Password': adminPassword }
    }),
    sendAdminTestEmail: (adminPassword, toEmail) => request('/admin/email/test', {
        method: 'POST',
        body: JSON.stringify({ to_email: toEmail || null }),
        headers: { 'X-Admin-Password': adminPassword }
    }),
    createBlogPost: (payload, adminPassword) => request('/blog/admin/posts', {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: { 'X-Admin-Password': adminPassword }
    }),
    updateBlogPost: (id, payload, adminPassword) => request(`/blog/admin/posts/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
        headers: { 'X-Admin-Password': adminPassword }
    }),
    deleteBlogPost: (id, adminPassword) => request(`/blog/admin/posts/${id}`, {
        method: 'DELETE',
        headers: { 'X-Admin-Password': adminPassword }
    }),
    getNewsletterCount: (adminPassword) => request('/admin/newsletter/count', {
        headers: { 'X-Admin-Password': adminPassword }
    }),
    
    // Onboarding personalization
    saveNiche: (niches) => request('/auth/save-niche', {
        method: 'POST',
        body: JSON.stringify({ niche_tags: niches }),
    }),
    saveVoiceSamples: (data) => request('/auth/save-voice-samples', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
    submitBugReport: (data) => request('/contact/bug-report', {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    // Generic request method for other endpoints
    request: (path, options = {}) => request(path, options),
};

export default api;
