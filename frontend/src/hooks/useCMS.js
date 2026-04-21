import { useState, useEffect } from 'react';
import { api } from '../utils/api';

/**
 * Custom hook to fetch CMS content for a specific page.
 * @param {string} page - The page identifier (e.g., 'home', 'pricing', 'global').
 * @param {object} defaults - Fallback values if the API fails or is loading.
 */
export const useCMS = (page, defaults = {}) => {
    const [content, setContent] = useState(defaults);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let isMounted = true;

        const fetchContent = async () => {
            try {
                setLoading(true);
                // Simple caching using a global object to avoid redundant fetches in the same session
                if (!window._cmsCache) window._cmsCache = {};
                
                if (window._cmsCache[page]) {
                    if (isMounted) {
                        setContent(prev => ({ ...prev, ...window._cmsCache[page] }));
                        setLoading(false);
                        return;
                    }
                }

                const data = await api.getCMSContent(page);
                
                if (isMounted) {
                    const mergedContent = { ...defaults, ...data };
                    setContent(mergedContent);
                    window._cmsCache[page] = data;
                    setError(null);
                }
            } catch (err) {
                console.error(`Failed to fetch CMS content for ${page}:`, err);
                if (isMounted) {
                    setError(err);
                    // Keep defaults on error
                    setContent(defaults);
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchContent();

        return () => {
            isMounted = false;
        };
    }, [page, JSON.stringify(defaults)]);

    return { content, loading, error };
};
