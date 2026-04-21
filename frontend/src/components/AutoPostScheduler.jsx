import React, { useState, useEffect } from 'react';
import { request } from '../utils/api';
import SocialPlatformIcon from './SocialPlatformIcon';

/**
 * AutoPostScheduler Component
 * Modal/panel for scheduling automatic posting to social media
 */
const AutoPostScheduler = ({ generationId, onClose, onScheduled }) => {
  const ENABLED_PLATFORMS = ['linkedin'];
  const [connectedAccounts, setConnectedAccounts] = useState([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchConnectedAccounts();
    
    // Set default date/time to tomorrow at 9 AM
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);
    
    setScheduleDate(tomorrow.toISOString().split('T')[0]);
    setScheduleTime('09:00');
  }, []);

  const fetchConnectedAccounts = async () => {
    try {
      const response = await request('/auth/social-accounts', {
        method: 'GET'
      });
      
      setConnectedAccounts(response.accounts || []);
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
      setError('Failed to load connected accounts');
    }
  };

  const togglePlatform = (platform) => {
    if (selectedPlatforms.includes(platform)) {
      setSelectedPlatforms(selectedPlatforms.filter(p => p !== platform));
    } else {
      setSelectedPlatforms([...selectedPlatforms, platform]);
    }
  };

  const scheduleAutoPost = async () => {
    const allowedSelectedPlatforms = selectedPlatforms.filter(platform => ENABLED_PLATFORMS.includes(platform));

    if (allowedSelectedPlatforms.length === 0) {
      setError('Please select at least one platform');
      return;
    }

    if (!scheduleDate || !scheduleTime) {
      setError('Please select date and time');
      return;
    }

    try {
      setLoading(true);
      setError('');

      // Combine date and time into ISO datetime
      const scheduledDateTime = new Date(`${scheduleDate}T${scheduleTime}`).toISOString();

      const response = await request(`/api/generate/${generationId}/schedule-auto-post`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          platforms: allowedSelectedPlatforms,
          schedule_time: scheduledDateTime,
          enabled: true
        })
      });

      if (response.success) {
        // Success
        if (onScheduled) {
          onScheduled();
        }
        if (onClose) {
          onClose();
        }
      } else {
        setError(response.error || 'Failed to schedule post');
      }
    } catch (err) {
      console.error('Failed to schedule:', err);
      setError('Failed to schedule auto-post. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const platformInfo = {
    twitter: { name: 'Twitter/X', icon: 'twitter', color: 'blue' },
    linkedin: { name: 'LinkedIn', icon: 'linkedin', color: 'blue' },
    instagram: { name: 'Instagram', icon: 'instagram', color: 'pink' }
  };
  const eligibleAccounts = connectedAccounts.filter(account => ENABLED_PLATFORMS.includes(account.platform));
  const hasPausedAccounts = connectedAccounts.some(account => !ENABLED_PLATFORMS.includes(account.platform));

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">
            🚀 Schedule Auto-Post
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Platform Selection */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Select Platforms
          </label>

          {eligibleAccounts.length === 0 ? (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
              ⚠️ No LinkedIn account connected. Please connect LinkedIn in Settings first.
            </div>
          ) : (
            <div className="space-y-2">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-700">
                LinkedIn-only mode is enabled right now.
              </div>
              {eligibleAccounts.map(account => {
                const info = platformInfo[account.platform];
                const isSelected = selectedPlatforms.includes(account.platform);

                return (
                  <button
                    key={account.platform}
                    onClick={() => togglePlatform(account.platform)}
                    className={`w-full p-3 rounded-lg border-2 transition flex items-center space-x-3 ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-[#18181B]">
                      <SocialPlatformIcon platform={info.icon} className="w-6 h-6" />
                    </div>
                    <div className="flex-1 text-left">
                      <div className="font-medium text-gray-800">{info.name}</div>
                      <div className="text-xs text-gray-500">@{account.username}</div>
                    </div>
                    <div>
                      {isSelected && (
                        <span className="text-blue-600 font-bold">✓</span>
                      )}
                    </div>
                  </button>
                );
              })}
              {hasPausedAccounts && (
                <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-600">
                  Twitter/X and Instagram are currently paused for auto-posting.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Date and Time Selection */}
        <div className="mb-6 grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Date
            </label>
            <input
              type="date"
              value={scheduleDate}
              onChange={(e) => setScheduleDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Time
            </label>
            <input
              type="time"
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Info Box */}
        <div className="mb-6 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
          <p>
            📅 Your content will be automatically posted at the scheduled time.
            Make sure your accounts stay connected!
          </p>
        </div>

        {/* Actions */}
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium"
          >
            Cancel
          </button>
          <button
            onClick={scheduleAutoPost}
            disabled={loading || eligibleAccounts.length === 0}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Scheduling...' : 'Schedule Post'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AutoPostScheduler;
