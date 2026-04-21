import { useState, useEffect } from 'react';
import { request } from '../utils/api';

/**
 * Hook to fetch and manage connected social media accounts
 * Can be used in any component to get current connected accounts
 */
export const useConnectedAccounts = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await request('/auth/social-accounts', {
        method: 'GET'
      });
      setAccounts(response.accounts || []);
    } catch (err) {
      console.error('Failed to fetch connected accounts:', err);
      setError(err.message || 'Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();

    // Listen for storage changes (OAuth callback from popup)
    const handleStorageChange = (e) => {
      if (e.key === 'oauth-completed') {
        fetchAccounts();
        localStorage.removeItem('oauth-completed');
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const isConnected = (platform) => {
    return accounts.some(acc => acc.platform === platform);
  };

  const getAccountInfo = (platform) => {
    return accounts.find(acc => acc.platform === platform);
  };

  return {
    accounts,
    loading,
    error,
    refetch: fetchAccounts,
    isConnected,
    getAccountInfo
  };
};
