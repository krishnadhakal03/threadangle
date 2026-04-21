import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import SocialPlatformIcon from './SocialPlatformIcon';

export default function Calendar() {
  const [calendarData, setCalendarData] = useState(null);
  const [currentWeekStart, setCurrentWeekStart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [selectedGenerationId, setSelectedGenerationId] = useState(null);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('09:00');

  useEffect(() => {
    loadCalendar();
  }, []);

  const loadCalendar = async (weekStart = null) => {
    try {
      setLoading(true);
      const url = weekStart 
        ? `/calendar/week?start_date=${weekStart}`
        : `/calendar/week`;
      
      const data = await api.request(url);
      setCalendarData(data);
      setCurrentWeekStart(data.week_start);
    } catch (error) {
      console.error('Failed to load calendar:', error);
      showToast('Failed to load calendar', 'error');
    } finally {
      setLoading(false);
    }
  };

  const markAsPosted = async (generationId) => {
    try {
      await api.request(`/generations/${generationId}/mark-posted`, {
        method: 'PUT'
      });
      showToast('✅ Marked as posted!');
      loadCalendar(currentWeekStart);
    } catch (error) {
      console.error('Failed to mark as posted:', error);
      showToast('Failed to mark as posted', 'error');
    }
  };

  const unschedulePost = async (generationId) => {
    try {
      await api.request(`/generations/${generationId}/unschedule`, {
        method: 'DELETE'
      });
      showToast('📅 Unscheduled');
      loadCalendar(currentWeekStart);
    } catch (error) {
      console.error('Failed to unschedule:', error);
      showToast('Failed to unschedule', 'error');
    }
  };

  const navigateWeek = (direction) => {
    if (!currentWeekStart) return;
    const date = new Date(currentWeekStart);
    date.setDate(date.getDate() + (direction === 'next' ? 7 : -7));
    loadCalendar(date.toISOString().split('T')[0]);
  };

  const showToast = (message, type = 'success') => {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed; top: 24px; right: 24px; z-index: 9999;
      background: ${type === 'error' ? '#EF4444' : '#10B981'};
      color: white; padding: 16px 24px; border-radius: 12px;
      font-size: 15px; font-weight: 600; box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  };

  if (loading && !calendarData) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-gray-400">Loading calendar...</div>
      </div>
    );
  }

  const weekDates = calendarData?.calendar ? Object.keys(calendarData.calendar) : [];
  const scheduledPostsThisWeek = calendarData?.total_scheduled || 0;

  const navigateDashboardTab = (tab) => {
    window.dispatchEvent(new CustomEvent('dashboard-change-tab', { detail: tab }));
  };

  return (
    <div className="min-h-screen bg-[#09090B] px-3 py-4 md:p-6">
      <div className="max-w-[1600px] mx-auto space-y-6">
        
        {/* Explanation Banner */}
        <div className="bg-[#18181B] border border-[#27272A] rounded-xl px-5 py-4 flex items-start gap-4">
          <span className="text-xl flex-shrink-0 mt-0.5">📅</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white mb-1">How Content Calendar works</p>
            <p className="text-xs text-[#71717A] leading-relaxed">
              Schedule any generated post and see your entire posting plan at a glance. Posts marked <span className="text-[#3B82F6] font-medium">⚡ auto-post</span> are automatically published to connected LinkedIn at the scheduled time. Posts without auto-post send you an email reminder to publish manually — you stay in full control.
            </p>
          </div>
          <a href="#" onClick={(e) => { e.preventDefault(); window.dispatchEvent(new CustomEvent('dashboard-change-tab', { detail: 'history' })); }} className="flex-shrink-0 text-[11px] font-semibold text-[#3B82F6] hover:text-white whitespace-nowrap">
            Schedule from History →
          </a>
        </div>

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">Content Calendar</h2>
            <p className="text-sm text-gray-400 mt-1">
              Schedule your posts and stay consistent
            </p>
          </div>
          
          {/* Week Navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigateWeek('prev')}
              className="p-2 bg-[#161B22] hover:bg-[#21262D] border border-[#21262D] hover:border-[#30363D] rounded-lg transition-colors"
            >
              <svg className="w-4 h-4 text-[#8B949E]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            <span className="text-sm text-[#C9D1D9] font-semibold px-3">
              {currentWeekStart && new Date(currentWeekStart).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              {' \u2013 '}
              {calendarData?.week_end && new Date(calendarData.week_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
            
            <button
              onClick={() => navigateWeek('next')}
              className="p-2 bg-[#161B22] hover:bg-[#21262D] border border-[#21262D] hover:border-[#30363D] rounded-lg transition-colors"
            >
              <svg className="w-4 h-4 text-[#8B949E]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            
            <button
              onClick={() => loadCalendar()}
              className="ml-2 px-3 py-1.5 bg-[#1F6FEB] hover:bg-[#388bfd] text-white text-sm font-semibold rounded-lg transition-colors"
            >
              Today
            </button>
          </div>
        </div>
        
        {/* Week View */}
        {scheduledPostsThisWeek === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 bg-[#0D1117] border border-[#21262D] rounded-2xl">
            <div className="w-16 h-16 rounded-2xl bg-[#161B22] border border-[#21262D] flex items-center justify-center mb-5">
              <svg className="w-8 h-8 text-[#484F58]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-white mb-2">No posts scheduled yet</h3>
            <p className="text-sm text-[#8B949E] mb-8 text-center max-w-sm">
              Generate content first, then schedule it from your History tab
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => navigateDashboardTab('dashboard')}
                className="px-5 py-2.5 bg-[#1F6FEB] hover:bg-[#388bfd] rounded-xl font-semibold text-white text-sm transition-colors"
              >
                Generate Content
              </button>
              <button
                onClick={() => navigateDashboardTab('history')}
                className="px-5 py-2.5 bg-[#161B22] hover:bg-[#21262D] border border-[#30363D] hover:border-[#484F58] rounded-xl font-semibold text-[#C9D1D9] text-sm transition-colors"
              >
                View History
              </button>
            </div>
          </div>
        ) : (
        <div className="grid grid-cols-7 gap-3">
          {weekDates.map((dateStr) => {
            const items = calendarData.calendar[dateStr];
            const date = new Date(dateStr);
            const today = new Date().toISOString().split('T')[0];
            const isToday = dateStr === today;
            const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
            const dayNumber = date.getDate();
            
            return (
              <div
                key={dateStr}
                className={`min-h-[250px] p-3 rounded-xl border transition-all ${
                  isToday
                    ? 'border-[#1F6FEB] bg-[#1F6FEB]/5'
                    : 'border-[#21262D] bg-[#0D1117] hover:border-[#30363D]'
                }`}
              >
                {/* Day Header */}
                <div className="mb-3">
                  <div className={`text-[10px] font-bold uppercase tracking-widest ${isToday ? 'text-[#388bfd]' : 'text-[#484F58]'}`}>
                    {dayName}
                  </div>
                  <div className={`text-lg font-bold mt-0.5 ${isToday ? 'text-[#388bfd]' : 'text-[#C9D1D9]'}`}>
                    {dayNumber}
                  </div>
                </div>
                
                {/* Scheduled Items */}
                <div className="space-y-2">
                  {items.length === 0 ? (
                    <div className="text-center py-8">
                      <div className="text-[#30363D] text-xs">—</div>
                    </div>
                  ) : (
                    items.map(item => {
                      const preview = item.twitter_preview || item.linkedin_preview || item.tiktok_preview || 'No content preview';
                      
                      return (
                        <div
                          key={item.id}
                          className={`p-2.5 rounded-lg border text-xs cursor-pointer transition-all ${
                            item.posted
                              ? 'border-emerald-500/30 bg-emerald-500/8'
                              : 'border-[#21262D] bg-[#161B22] hover:border-[#30363D]'
                          }`}
                        >
                          {/* Time */}
                          {item.scheduled_time && (
                            <div className={`font-bold mb-1.5 ${item.posted ? 'text-emerald-400' : 'text-[#388bfd]'}`}>
                              {item.scheduled_time}
                            </div>
                          )}
                          
                          {/* Auto-Post Status Badge */}
                          {item.auto_post_enabled && (
                            <div className="flex items-center gap-1 text-[#388bfd] mb-2 text-[10px] font-semibold">
                              <svg className="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
                              </svg>
                              Auto-post
                            </div>
                          )}
                          
                          {/* Platforms */}
                          <div className="flex flex-wrap gap-1 mb-2">
                            {(item.platforms?.includes('all') || item.platforms?.includes('twitter')) && (
                              <span className="px-1.5 py-0.5 bg-[#1DA1F2]/15 text-[#1DA1F2] rounded text-[9px] font-bold">X</span>
                            )}
                            {(item.platforms?.includes('all') || item.platforms?.includes('linkedin')) && (
                              <span className="px-1.5 py-0.5 bg-[#0A66C2]/15 text-[#0A66C2] rounded text-[9px] font-bold">in</span>
                            )}
                            {(item.platforms?.includes('all') || item.platforms?.includes('tiktok')) && (
                              <span className="px-1.5 py-0.5 bg-pink-500/15 text-pink-400 rounded text-[9px] font-bold">TT</span>
                            )}
                          </div>
                          
                          {/* Preview */}
                          <div className="text-[#8B949E] line-clamp-2 mb-2 leading-relaxed">
                            {preview}
                          </div>
                          
                          {/* Auto-Posted Status */}
                          {item.auto_posted_at && (
                            <div className="text-emerald-400 text-[10px] font-semibold mb-2">
                              ✓ Auto-posted {new Date(item.auto_posted_at).toLocaleDateString()}
                            </div>
                          )}
                          
                          {/* Actions */}
                          <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#21262D]">
                            {!item.posted && !item.auto_posted_at ? (
                              <button
                                onClick={(e) => { e.stopPropagation(); markAsPosted(item.id); }}
                                className="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[10px] font-semibold transition-colors"
                              >
                                Mark Posted
                              </button>
                            ) : (
                              <div className="flex items-center gap-1 text-emerald-400">
                                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                <span className="text-[10px] font-semibold">Posted</span>
                              </div>
                            )}
                            <button
                              onClick={(e) => { e.stopPropagation(); unschedulePost(item.id); }}
                              className="text-[#484F58] hover:text-red-400 transition-colors"
                            >
                              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
        )}
        
        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-4 p-5 bg-[#0D1117] rounded-2xl border border-[#21262D]">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#388bfd]">
              {calendarData?.total_scheduled || 0}
            </div>
            <div className="text-xs text-[#8B949E] mt-1 font-medium">Scheduled This Week</div>
          </div>
          <div className="text-center border-x border-[#21262D]">
            <div className="text-2xl font-bold text-emerald-400">
              {calendarData?.calendar ?
                Object.values(calendarData.calendar).flat().filter(item => item.posted).length
                : 0}
            </div>
            <div className="text-xs text-[#8B949E] mt-1 font-medium">Posted</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-amber-400">
              {calendarData?.calendar ?
                Object.values(calendarData.calendar).flat().filter(item => !item.posted).length
                : 0}
            </div>
            <div className="text-xs text-[#8B949E] mt-1 font-medium">Pending</div>
          </div>
        </div>
        
      </div>
    </div>
  );
}
